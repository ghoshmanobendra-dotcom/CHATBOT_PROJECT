"""
Stage 2 - GCECT IT Department FAQ Chatbot (knowledge base + keyword scoring)

HOW TO CUSTOMISE:
  1. All college data lives in INFO, SYLLABUS and SUBJECTS below.
  2. Any value left as "[TO BE UPDATED]" makes the bot reply that the
     information is not available yet (and shows the department contact).
  3. Add new questions by adding a new entry to the FAQ list.
"""

import re
import difflib
from datetime import datetime

TODO = "[TO BE UPDATED]"
UNANSWERED_LOG = "unanswered_questions.txt"

# ----------------------------------------------------------------------
# 1. COLLEGE DATA
# ----------------------------------------------------------------------
INFO = {
    "college_name": "Government College of Engineering & Ceramic Technology",
    "short_name": "GCECT",
    "affiliation": "An Autonomous Institution under MAKUT",
    "city": "Kolkata",
    "address": "73, Abinash Chandra Banerjee Ln, Subhas Sarobar Park, Phoolbagan, "
               "Beleghata, Kolkata, West Bengal 700010",
    "website": "https://gcect.ac.in/",
    "dept": "Information Technology",
    "building": "Administrative Building",
    "dept_floor": "3",
    "hod_name": "Prof. (Dr.) Mausumi Maitra (Mazumdar)",
    "hod_room": "301",
    "hod_floor": "3",
    "dept_hours": "10 AM to 5 PM",
    "library_hours": "10 AM to 5 PM",
    "lab_hours": "2:10 PM to 5 PM",
    "exam_timing": "12 PM to 3 PM",
    "exam_link": "https://gcect.ac.in/semester-examination-schedule/",
    "syllabus_link": TODO,
    "faculty_link": "https://gcect.ac.in/department-of-information-technology/",
    "placement_link": "https://gcect.ac.in/training-placement-dept-of-it/",
    "holiday_link": "https://gcect.ac.in/download/Miscellaneous/GCECT-Holiday-List-2026.pdf",
    "fees": "Rs. 13,200",
    "scholarships": "Student Freeship and SVMCM (Swami Vivekananda Merit cum Means scholarship)",
    "clubs": "Bytemonk",
    "hostel": TODO,
    "admission_docs": "Aadhaar card, PAN card, ration card, domicile certificate, "
                      "Class 10 and Class 12 marksheets, caste certificate, income certificate",
    "email": "gcect.it@gmail.com",
    "phone": "123456789",
}

# Semester-wise course structure (B.Tech IT, curriculum 2024-25 onwards)
SYLLABUS = {
    1: {
        "credits": "16",
        "theory": "Mathematics-I, Physics, Basic Electrical Engineering, English",
        "lab": "Physics Lab, Basic Electrical Engineering Lab, Engineering Graphics & Design, "
               "English Communication Lab",
        "note": "Includes a mandatory 3-week induction program.",
    },
    2: {
        "credits": "22.5",
        "theory": "Mathematics-II, Chemistry, Programming for Problem Solving, "
                  "Analog and Digital Electronics, Universal Human Values",
        "lab": "Chemistry Lab, Programming for Problem Solving Lab, Workshop/Manufacturing Practices, "
               "Electronics Lab, Design Thinking Lab, NSS",
        "note": "2 to 4 weeks summer training/internship, evaluated in 3rd semester.",
    },
    3: {
        "credits": "26",
        "theory": "Mathematics-III, Communication Engineering, Computer Organization, "
                  "Data Structure & Algorithms, Economics for Engineers, Environmental Sciences",
        "lab": "Computer Organization Lab, Data Structure & Algorithms Lab, IT Workshop (Python), "
               "Communication Engineering Lab, Summer Internship 1",
        "note": "",
    },
    4: {
        "credits": "24",
        "theory": "Discrete Mathematics, Design & Analysis of Algorithm, "
                  "Formal Language and Automata Theory, Computer Architecture, "
                  "Biology for Engineers, Constitution of India",
        "lab": "Algorithm Lab, Programming Lab using C++, Project 1 (part 1)",
        "note": "2 to 4 weeks summer training/internship, evaluated in 5th semester.",
    },
    5: {
        "credits": "25.5",
        "theory": "Operating Systems, Database Management System, Object Oriented Programming, "
                  "Artificial Intelligence, Open Elective-1 (Control System / Microprocessor and "
                  "Interfacing / Digital Signal Processing / Advanced Computer Architecture)",
        "lab": "Operating System Lab, Database Management System Lab, Programming Lab using Java, "
               "Open Elective-I Lab, Project 1 (part 2), Summer Internship 2",
        "note": "",
    },
    6: {
        "credits": "25",
        "theory": "Computer Networks, Compiler Design, Software Engineering, "
                  "Introduction to Cyber Security, Elective-I, Open Elective-II",
        "lab": "Computer Network Lab, Software Engineering Lab, Elective-I Lab, Project 1 (part 3)",
        "note": "4 to 6 weeks industrial training in summer, evaluated in 7th semester.",
    },
    7: {
        "credits": "20",
        "theory": "Elective-II, Elective-III, Elective-IV, Open Elective-III, Industrial Management",
        "lab": "Project 2 / Internship / Industrial Project, Industrial Training",
        "note": "",
    },
    8: {
        "credits": "7",
        "theory": "No theory papers",
        "lab": "Project 3 / Internship / Industrial Project, Comprehensive Viva Voce",
        "note": "",
    },
}

# Detailed information for individual subjects (semesters 3 to 5)
SUBJECTS = [
    {"name": "Mathematics-III", "code": "BS(IT)307", "sem": 3, "credits": 3, "ltp": "3-0-0",
     "aliases": ["mathematics iii", "mathematics 3", "maths iii", "maths 3", "math 3", "math iii"],
     "topics": "Fourier series and transforms; multivariable calculus (differentiation and "
               "integration); ordinary differential equations; graph theory."},
    {"name": "Communication Engineering", "code": "ES(IT)309", "sem": 3, "credits": 3, "ltp": "3-0-0",
     "aliases": ["communication engineering", "communication engg"],
     "topics": "AM, FM and PM; sampling, PCM and digital modulation (ASK, FSK, PSK); "
               "line codes; wireless and cellular communication basics."},
    {"name": "Computer Organization", "code": "PC(IT)301", "sem": 3, "credits": 4, "ltp": "3-1-0",
     "aliases": ["computer organization", "computer organisation", "co"],
     "topics": "Instruction set and processor design; control unit design; memory subsystem; "
               "peripherals and I/O (DMA, RAID); pipelining."},
    {"name": "Data Structure & Algorithms", "code": "PC(IT)302", "sem": 3, "credits": 4, "ltp": "3-1-0",
     "aliases": ["data structure", "data structure and algorithm", "dsa", "ds"],
     "topics": "Algorithm analysis; arrays, linked lists, stacks, queues; trees, heaps, graphs; "
               "searching and sorting; hashing."},
    {"name": "Economics for Engineers", "code": "HS(IT)305", "sem": 3, "credits": 3, "ltp": "3-0-0",
     "aliases": ["economics for engineers", "economics"],
     "topics": "Cost concepts and break-even analysis; cash flow and interest; capital budgeting "
               "(NPV, IRR); risk and inflation; depreciation and accounting basics."},
    {"name": "Environmental Sciences", "code": "BS(IT)308", "sem": 3, "credits": 2, "ltp": "2-0-0",
     "aliases": ["environmental sciences", "environmental science", "evs"],
     "topics": "Green computing; carbon footprint; e-waste; social issues and the environment; "
               "green technologies."},
    {"name": "Discrete Mathematics", "code": "BS(IT)409", "sem": 4, "credits": 3, "ltp": "3-0-0",
     "aliases": ["discrete mathematics", "discrete math", "discrete maths"],
     "topics": "Number theory; counting and recurrence relations; propositional logic; "
               "algebraic structures and Boolean algebra; planar graphs and graph colouring."},
    {"name": "Design & Analysis of Algorithm", "code": "PC(IT)406", "sem": 4, "credits": 4, "ltp": "3-1-0",
     "aliases": ["design and analysis of algorithm", "daa", "analysis of algorithm"],
     "topics": "Design paradigms (divide and conquer, greedy, dynamic programming, backtracking); "
               "sorting; graph algorithms; string matching; amortized analysis; P and NP."},
    {"name": "Formal Language and Automata Theory", "code": "PC(IT)407", "sem": 4, "credits": 4,
     "ltp": "3-1-0",
     "aliases": ["formal language and automata theory", "automata", "flat", "toc",
                 "theory of computation"],
     "topics": "Finite automata and regular languages; context-free grammars and pushdown automata; "
               "context-sensitive languages; Turing machines; undecidability."},
    {"name": "Computer Architecture", "code": "PC(IT)408", "sem": 4, "credits": 4, "ltp": "3-1-0",
     "aliases": ["computer architecture", "coa"],
     "topics": "Pipelining and hazards; memory modules; cache and virtual memory; "
               "instruction-level parallelism (RISC, VLIW); multiprocessors; VHDL and CAD tools."},
    {"name": "Biology for Engineers", "code": "ES(IT)411", "sem": 4, "credits": 3, "ltp": "3-0-0",
     "aliases": ["biology for engineers", "biology"],
     "topics": "Cells and biomolecules; genetics; medical imaging; human physiology; "
               "biotechnology and synthetic biology."},
    {"name": "Constitution of India", "code": "HS(IT)406", "sem": 4, "credits": 2, "ltp": "2-0-0",
     "aliases": ["constitution of india", "constitution"],
     "topics": "Indian Constitution basics; union and state executive; legal system; "
               "IPR and IT Act; business organizations and e-governance."},
    {"name": "Operating Systems", "code": "PC(IT)511", "sem": 5, "credits": 4, "ltp": "3-1-0",
     "aliases": ["operating system", "os"],
     "topics": "Processes and threads; CPU scheduling, synchronization, deadlocks; memory management "
               "and virtual memory; file systems; disk and I/O management; protection and security."},
    {"name": "Database Management System", "code": "PC(IT)512", "sem": 5, "credits": 4, "ltp": "3-1-0",
     "aliases": ["database management system", "dbms", "database"],
     "topics": "ER model; relational algebra and SQL; normalization; transactions and concurrency "
               "control; indexing and B+ trees."},
    {"name": "Object Oriented Programming", "code": "PC(IT)513", "sem": 5, "credits": 4, "ltp": "3-1-0",
     "aliases": ["object oriented programming", "oop", "java"],
     "topics": "OOP concepts and Java basics; inheritance, polymorphism, abstract classes, interfaces, "
               "packages; exception handling; multithreading; applets."},
    {"name": "Artificial Intelligence", "code": "PC(IT)514", "sem": 5, "credits": 3, "ltp": "3-0-0",
     "aliases": ["artificial intelligence", "ai"],
     "topics": "Intelligent agents; search techniques (BFS, A*, minimax); knowledge and reasoning; "
               "machine learning and planning; generative AI tools and applications."},
]

# ----------------------------------------------------------------------
# 2. TEXT PROCESSING
# ----------------------------------------------------------------------
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "am", "be", "of", "in",
    "on", "at", "to", "for", "me", "my", "please", "tell", "about", "can",
    "you", "i", "do", "does", "and", "or", "it", "there", "any", "give",
}

EXIT_WORDS = {"bye", "exit", "quit"}


def stem(word):
    """Very light stemming: 'timings' -> 'timing', 'labs' -> 'lab'."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def normalize(text):
    """Lowercase, remove punctuation, and return a clean string."""
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def stem_text(text):
    return " ".join(stem(w) for w in normalize(text).split())


# ----------------------------------------------------------------------
# 3. KNOWLEDGE BASE
#    keywords : single words (each match = 1 point)
#    phrases  : multi-word expressions (each match = 3 points)
#    answer   : text; {name} placeholders are filled from INFO
# ----------------------------------------------------------------------
FAQ = [
    {
        "topic": "Greeting",
        "keywords": {"hello", "hi", "hey", "namaste", "morning", "afternoon", "evening"},
        "phrases": ["good morning", "good afternoon", "good evening"],
        "answer": "Hello! I am the {short_name} {dept} Department assistant. "
                  "Type 'help' to see what I can answer.",
    },
    {
        "topic": "Thanks",
        "keywords": {"thank", "thanks", "thankyou"},
        "phrases": ["thank you"],
        "answer": "You're welcome! Ask me anything else about the department.",
    },
    {
        "topic": "About the college",
        "keywords": {"college", "institute", "name", "full", "city", "university",
                     "autonomous", "makaut", "affiliation"},
        "phrases": ["full name", "college name", "which college", "about college"],
        "answer": "{college_name} ({short_name}), {city}.\n{affiliation}.\n"
                  "Address: {address}\nWebsite: {website}",
    },
    {
        "topic": "Head of Department (HOD)",
        "keywords": {"hod", "head", "cabin", "room", "who"},
        "phrases": ["head of department", "hod office", "hod room", "hod cabin"],
        "answer": "The HOD of {dept} is {hod_name}.\n"
                  "Office: Room {hod_room}, Floor {hod_floor}, {building}.",
    },
    {
        "topic": "Faculty",
        "keywords": {"faculty", "teacher", "professor", "staff", "lecturer", "teach"},
        "phrases": ["faculty list", "faculty members", "who teaches"],
        "answer": "You can see the {dept} faculty list here: {faculty_link}",
    },
    {
        "topic": "Department location",
        "keywords": {"where", "location", "located", "building", "floor",
                     "department", "dept", "find", "reach", "address"},
        "phrases": ["where is the department", "how to reach"],
        "answer": "The {dept} Department is on Floor {dept_floor} of the {building}, "
                  "{college_name}.\nAddress: {address}",
    },
    {
        "topic": "Department timings",
        "keywords": {"department", "dept", "timing", "time", "hour", "open", "close"},
        "phrases": ["department timing", "office timing", "office hours"],
        "answer": "Department office hours: {dept_hours}.",
    },
    {
        "topic": "Library timings",
        "keywords": {"library", "book", "librarian", "timing", "time", "hour", "open", "close"},
        "phrases": ["library timing", "library hours"],
        "answer": "Library hours: {library_hours}.",
    },
    {
        "topic": "Laboratory timings",
        "keywords": {"lab", "laboratory", "practical", "timing", "time", "hour"},
        "phrases": ["lab timing", "lab hours", "practical class"],
        "answer": "Laboratory / practical class timing: {lab_hours}.",
    },
    {
        "topic": "Syllabus and subjects",
        "keywords": {"syllabus", "curriculum", "subject", "course", "semester",
                     "sem", "year", "paper", "taught", "study"},
        "phrases": ["what subjects", "subjects taught", "course structure"],
        "answer": "Ask for a specific semester or year, e.g. '3rd semester subjects', "
                  "'2nd year subjects', or a subject name like 'operating systems'.",
    },
    {
        "topic": "Exam timing",
        "keywords": {"exam", "examination", "timing", "time", "hour", "duration", "shift"},
        "phrases": ["exam timing", "exam time", "examination time", "what time exam"],
        "answer": "Examination timing: {exam_timing}.",
    },
    {
        "topic": "Exam routine / schedule",
        "keywords": {"exam", "examination", "routine", "schedule", "timetable",
                     "date", "when"},
        "phrases": ["exam routine", "exam schedule", "exam date", "time table",
                    "when is the exam", "when are the exams"],
        "answer": "Semester examination schedule / routine: {exam_link}",
    },
    {
        "topic": "Exam pattern and marks",
        "keywords": {"marks", "pattern", "internal", "mid", "assessment", "grading",
                     "credit", "pass"},
        "phrases": ["exam pattern", "mid sem", "mid semester", "end semester", "internal marks"],
        "answer": "For most theory papers: 50 marks internal (Mid-Semester 1: 15, Mid-Semester 2: 15, "
                  "assignments/quiz/attendance: 20) and an End Semester Exam of 100 marks that is "
                  "converted to 50, giving 100 in total. Lab papers are graded on attendance, lab "
                  "report, experimental work, presentation and viva. Marks can vary slightly by subject.",
    },
    {
        "topic": "Internship and training",
        "keywords": {"internship", "industrial", "training", "summer", "intern"},
        "phrases": ["summer internship", "industrial training"],
        "answer": "Summer internships (2 to 4 weeks) follow 2nd and 4th semesters and are evaluated in "
                  "3rd and 5th semesters. A 4 to 6 week industrial training follows 6th semester and is "
                  "evaluated in 7th semester. 7th and 8th semesters also include a project / internship / "
                  "industrial project.",
    },
    {
        "topic": "Admission documents",
        "keywords": {"admission", "document", "certificate", "required", "apply",
                     "admit", "join"},
        "phrases": ["documents required", "how to apply", "required documents"],
        "answer": "Documents required for admission: {admission_docs}.",
    },
    {
        "topic": "Fees",
        "keywords": {"fee", "tuition", "cost", "payment", "charge"},
        "phrases": ["how much", "fee structure"],
        "answer": "Fees: {fees}. Please confirm the latest fee details with the college office.",
    },
    {
        "topic": "Scholarships",
        "keywords": {"scholarship", "freeship", "svmcm", "stipend", "financial", "aid"},
        "phrases": ["financial aid", "student freeship"],
        "answer": "Scholarships and financial support: {scholarships}.",
    },
    {
        "topic": "Placement and training cell",
        "keywords": {"placement", "placed", "recruit", "company", "job", "package", "tnp"},
        "phrases": ["training and placement", "placement cell"],
        "answer": "Training & Placement details for the {dept} department: {placement_link}",
    },
    {
        "topic": "Clubs and technical activities",
        "keywords": {"club", "fest", "technical", "bytemonk", "event", "society", "activity"},
        "phrases": ["tech fest", "technical club"],
        "answer": "Clubs / technical activities: {clubs}.",
    },
    {
        "topic": "Hostel",
        "keywords": {"hostel", "accommodation", "stay", "mess", "boarding"},
        "phrases": ["hostel facility"],
        "answer": "Hostel information: {hostel}",
    },
    {
        "topic": "Holidays and academic calendar",
        "keywords": {"holiday", "calendar", "vacation", "academic", "leave"},
        "phrases": ["holiday list", "academic calendar"],
        "answer": "Holiday list / academic calendar: {holiday_link}",
    },
    {
        "topic": "College website",
        "keywords": {"website", "site", "link", "portal", "online", "url"},
        "phrases": ["official website", "college website"],
        "answer": "Official website: {website}",
    },
    {
        "topic": "Contact details",
        "keywords": {"contact", "email", "mail", "phone", "call", "number", "reach"},
        "phrases": ["contact number", "phone number", "email id"],
        "answer": "Department email: {email}\nDepartment phone: {phone}",
    },
]

# Stem all keywords once so they match the stemmed user words
for _entry in FAQ:
    _entry["keywords"] = {stem(k) for k in _entry["keywords"]}

# Vocabulary used for spelling correction
VOCAB = sorted({k for e in FAQ for k in e["keywords"]})


def correct_spelling(word):
    """Fix small typos: 'libary' -> 'library', 'sylabus' -> 'syllabus'."""
    if word in VOCAB or len(word) < 4 or word.isdigit():
        return word
    match = difflib.get_close_matches(word, VOCAB, n=1, cutoff=0.8)
    return match[0] if match else word


def get_words(text):
    """Tokenize -> remove stopwords -> stem -> correct spelling."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    words = [stem(w) for w in words if w not in STOPWORDS]
    return {correct_spelling(w) for w in words}


# ----------------------------------------------------------------------
# 4. SEMESTER AND SUBJECT DETECTION
# ----------------------------------------------------------------------
ORDINALS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4,
    "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
}
NUM = r"(\d|first|second|third|fourth|fifth|sixth|seventh|eighth)"


def to_number(token):
    return int(token) if token.isdigit() else ORDINALS[token]


def extract_semesters(text):
    """'3rd semester' -> [3];  '2nd year' -> [3, 4];  'sem 5' -> [5]."""
    t = text.lower()

    m = re.search(NUM + r"(?:st|nd|rd|th)?\s*(?:sem|semester)\b", t) \
        or re.search(r"\b(?:sem|semester)\s*" + NUM + r"\b", t)
    if m:
        sem = to_number(m.group(1))
        return [sem] if 1 <= sem <= 8 else []

    m = re.search(NUM + r"(?:st|nd|rd|th)?\s*year\b", t)
    if m:
        year = to_number(m.group(1))
        if 1 <= year <= 4:
            return [2 * year - 1, 2 * year]
    return []


def format_semester(sem):
    data = SYLLABUS[sem]
    lines = [
        f"Semester {sem} ({data['credits']} credits)",
        f"  Theory: {data['theory']}",
        f"  Labs / Sessional: {data['lab']}",
    ]
    if data["note"]:
        lines.append(f"  Note: {data['note']}")
    return "\n".join(lines)


def syllabus_answer(question):
    semesters = extract_semesters(question)
    if not semesters:
        return None
    text = "\n\n".join(format_semester(s) for s in semesters)
    if INFO["syllabus_link"] != TODO:
        text += f"\n\nFull syllabus: {INFO['syllabus_link']}"
    return text


def find_subject(question):
    """Return the SUBJECTS entry mentioned in the question (longest alias wins)."""
    stemmed = stem_text(question)
    best, best_len = None, 0
    for subject in SUBJECTS:
        for alias in subject["aliases"]:
            a = stem_text(alias)
            if len(a) > best_len and re.search(r"\b" + re.escape(a) + r"\b", stemmed):
                best, best_len = subject, len(a)
    return best


def subject_answer(subject):
    return (f"{subject['name']} ({subject['code']}) - Semester {subject['sem']}, "
            f"{subject['credits']} credits (L-T-P: {subject['ltp']}).\n"
            f"Topics: {subject['topics']}")


# ----------------------------------------------------------------------
# 5. MATCHING ENGINE
# ----------------------------------------------------------------------
def score_entry(entry, words, clean_text):
    score = len(words & entry["keywords"])
    score += 3 * sum(1 for p in entry["phrases"] if p in clean_text)
    return score


def render(entry):
    """Fill the answer template; fall back if some data is still missing."""
    text = entry["answer"].format(**INFO)
    if TODO in text:
        return ("I don't have this information yet. Please contact the department:\n"
                f"Email: {INFO['email']}\nPhone: {INFO['phone']}")
    return text


def find_answer(question):
    """
    Returns (kind, payload):
      ("answer", text)          - one clear best match
      ("clarify", [topics])     - several equally good matches
      ("none", None)            - nothing matched
    """
    # 1) A specific subject was mentioned (e.g. "operating systems syllabus")
    subject = find_subject(question)
    if subject:
        return "answer", subject_answer(subject)

    # 2) Score every FAQ entry
    words = get_words(question)
    clean_text = normalize(question)

    scored = [(score_entry(e, words, clean_text), e) for e in FAQ]
    best = max(s for s, _ in scored)

    if best == 0:
        return "none", None

    winners = [e for s, e in scored if s == best]

    if len(winners) > 1:
        return "clarify", [e["topic"] for e in winners]

    entry = winners[0]

    # 3) Syllabus questions with a semester/year get a detailed answer
    if entry["topic"] == "Syllabus and subjects":
        special = syllabus_answer(question)
        if special:
            return "answer", special

    return "answer", render(entry)


# ----------------------------------------------------------------------
# 6. HELPERS
# ----------------------------------------------------------------------
def log_unanswered(question):
    with open(UNANSWERED_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} | {question}\n")


def show_help():
    print("Bot: I can help with these topics:")
    for entry in FAQ[2:]:
        print("  -", entry["topic"])
    print("You can also ask about a subject, e.g. 'DBMS syllabus' or '4th semester subjects'.")
    print("Type 'bye' to exit.")


def warn_missing_data():
    missing = [k for k, v in INFO.items() if v == TODO]
    if missing:
        print("[Note] Still to be filled in INFO: " + ", ".join(missing))
        print()


# ----------------------------------------------------------------------
# 7. MAIN LOOP
# ----------------------------------------------------------------------
def main():
    print(f"{INFO['short_name']} {INFO['dept']} FAQ Chatbot")
    print("Type 'help' for topics, 'bye' to exit.\n")
    warn_missing_data()

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Goodbye!")
            break

        if not question:
            continue

        clean = set(normalize(question).split())
        if clean & EXIT_WORDS:
            print("Bot: Thank you! Goodbye!")
            break

        if clean == {"help"}:
            show_help()
            continue

        kind, payload = find_answer(question)

        if kind == "answer":
            print("Bot:", payload)
        elif kind == "clarify":
            print("Bot: Did you mean one of these?")
            for topic in payload:
                print("  -", topic)
        else:
            print("Bot: Sorry, I don't know the answer. Type 'help' to see topics.")
            log_unanswered(question)

        print()


if __name__ == "__main__":
    main()
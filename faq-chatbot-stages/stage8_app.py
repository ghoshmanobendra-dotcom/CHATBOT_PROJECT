"""
Stage 8 — GCECT IT Department Chatbot (Web Interface)
======================================================
This module wraps the full Stage-2 knowledge-base logic (keyword scoring,
syllabus parsing, individual-subject lookup) inside a Flask web app.

Architecture:
    Browser (index.html + JS)
        -> POST /chat  {"message": "..."}
        -> Flask route in this file
        -> Knowledge-base engine (keyword + phrase scoring,
           subject lookup, semester detection)
        -> JSON response {"response": "..."}
        -> JS updates the chat window

Run:
    pip install flask scikit-learn
    python stage8_app.py
Then open http://127.0.0.1:5000 in your browser.
"""

import re
import json
import random
import difflib
from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# -----------------------------------------------------------------------
# COLLEGE DATA  (all details for GCECT IT Department)
# -----------------------------------------------------------------------
INFO = {
    "college_name": "Government College of Engineering & Ceramic Technology",
    "short_name":   "GCECT",
    "affiliation":  "An Autonomous Institution under MAKAUT",
    "city":         "Kolkata",
    "address": (
        "73, Abinash Chandra Banerjee Ln, Subhas Sarobar Park, "
        "Phoolbagan, Beleghata, Kolkata, West Bengal 700010"
    ),
    "website":        "https://gcect.ac.in/",
    "dept":           "Information Technology",
    "building":       "Administrative Building",
    "dept_floor":     "3",
    "hod_name":       "Prof. (Dr.) Mausumi Maitra (Mazumdar)",
    "hod_room":       "301",
    "hod_floor":      "3",
    "dept_hours":     "10 AM to 5 PM",
    "library_hours":  "10 AM to 5 PM",
    "lab_hours":      "2:10 PM to 5 PM",
    "exam_timing":    "12 PM to 3 PM",
    "exam_link":      "https://gcect.ac.in/semester-examination-schedule/",
    "faculty_link":   "https://gcect.ac.in/department-of-information-technology/",
    "placement_link": "https://gcect.ac.in/training-placement-dept-of-it/",
    "holiday_link":   "https://gcect.ac.in/download/Miscellaneous/GCECT-Holiday-List-2026.pdf",
    "fees":           "Rs. 13,200",
    "scholarships":   "Student Freeship and SVMCM (Swami Vivekananda Merit cum Means Scholarship)",
    "clubs":          "Bytemonk (IT technical club)",
    "admission_docs": (
        "Aadhaar card, PAN card, ration card, domicile certificate, "
        "Class 10 and Class 12 marksheets, caste certificate, income certificate"
    ),
    "email": "gcect.it@gmail.com",
    "phone": "123456789",
}

# Semester-wise course structure
SYLLABUS = {
    1: {
        "credits": "16",
        "theory": "Mathematics-I, Physics, Basic Electrical Engineering, English",
        "lab": (
            "Physics Lab, Basic Electrical Engineering Lab, "
            "Engineering Graphics & Design, English Communication Lab"
        ),
        "note": "Includes a mandatory 3-week induction program.",
    },
    2: {
        "credits": "22.5",
        "theory": (
            "Mathematics-II, Chemistry, Programming for Problem Solving, "
            "Analog and Digital Electronics, Universal Human Values"
        ),
        "lab": (
            "Chemistry Lab, Programming for Problem Solving Lab, "
            "Workshop/Manufacturing Practices, Electronics Lab, "
            "Design Thinking Lab, NSS"
        ),
        "note": "2 to 4 weeks summer training/internship, evaluated in 3rd semester.",
    },
    3: {
        "credits": "26",
        "theory": (
            "Mathematics-III, Communication Engineering, Computer Organization, "
            "Data Structure & Algorithms, Economics for Engineers, Environmental Sciences"
        ),
        "lab": (
            "Computer Organization Lab, Data Structure & Algorithms Lab, "
            "IT Workshop (Python), Communication Engineering Lab, Summer Internship 1"
        ),
        "note": "",
    },
    4: {
        "credits": "24",
        "theory": (
            "Discrete Mathematics, Design & Analysis of Algorithm, "
            "Formal Language and Automata Theory, Computer Architecture, "
            "Biology for Engineers, Constitution of India"
        ),
        "lab": "Algorithm Lab, Programming Lab using C++, Project 1 (part 1)",
        "note": "2 to 4 weeks summer training/internship, evaluated in 5th semester.",
    },
    5: {
        "credits": "25.5",
        "theory": (
            "Operating Systems, Database Management System, Object Oriented Programming, "
            "Artificial Intelligence, Open Elective-1 (Control System / Microprocessor and "
            "Interfacing / Digital Signal Processing / Advanced Computer Architecture)"
        ),
        "lab": (
            "Operating System Lab, Database Management System Lab, "
            "Programming Lab using Java, Open Elective-I Lab, "
            "Project 1 (part 2), Summer Internship 2"
        ),
        "note": "",
    },
    6: {
        "credits": "25",
        "theory": (
            "Computer Networks, Compiler Design, Software Engineering, "
            "Introduction to Cyber Security, Elective-I, Open Elective-II"
        ),
        "lab": (
            "Computer Network Lab, Software Engineering Lab, "
            "Elective-I Lab, Project 1 (part 3)"
        ),
        "note": "4 to 6 weeks industrial training in summer, evaluated in 7th semester.",
    },
    7: {
        "credits": "20",
        "theory": (
            "Elective-II, Elective-III, Elective-IV, "
            "Open Elective-III, Industrial Management"
        ),
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

# Individual subject details (Sem 3–5 with full topic coverage)
SUBJECTS = [
    {
        "name": "Mathematics-III", "code": "BS(IT)307", "sem": 3,
        "credits": 3, "ltp": "3-0-0",
        "aliases": ["mathematics iii", "mathematics 3", "maths iii",
                    "maths 3", "math 3", "math iii", "maths3"],
        "topics": (
            "Fourier series and transforms; multivariable calculus "
            "(differentiation and integration); ordinary differential equations; graph theory."
        ),
    },
    {
        "name": "Communication Engineering", "code": "ES(IT)309", "sem": 3,
        "credits": 3, "ltp": "3-0-0",
        "aliases": ["communication engineering", "communication engg", "comm engg"],
        "topics": (
            "AM, FM and PM; sampling, PCM and digital modulation (ASK, FSK, PSK); "
            "line codes; wireless and cellular communication basics."
        ),
    },
    {
        "name": "Computer Organization", "code": "PC(IT)301", "sem": 3,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["computer organization", "computer organisation", "co"],
        "topics": (
            "Instruction set and processor design; control unit design; memory subsystem; "
            "peripherals and I/O (DMA, RAID); pipelining."
        ),
    },
    {
        "name": "Data Structure & Algorithms", "code": "PC(IT)302", "sem": 3,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["data structure", "data structure and algorithm",
                    "dsa", "ds", "data structures"],
        "topics": (
            "Algorithm analysis; arrays, linked lists, stacks, queues; "
            "trees, heaps, graphs; searching and sorting; hashing."
        ),
    },
    {
        "name": "Economics for Engineers", "code": "HS(IT)305", "sem": 3,
        "credits": 3, "ltp": "3-0-0",
        "aliases": ["economics for engineers", "economics"],
        "topics": (
            "Cost concepts and break-even analysis; cash flow and interest; "
            "capital budgeting (NPV, IRR); risk and inflation; depreciation and accounting basics."
        ),
    },
    {
        "name": "Environmental Sciences", "code": "BS(IT)308", "sem": 3,
        "credits": 2, "ltp": "2-0-0",
        "aliases": ["environmental sciences", "environmental science", "evs"],
        "topics": (
            "Green computing; carbon footprint; e-waste; "
            "social issues and the environment; green technologies."
        ),
    },
    {
        "name": "Discrete Mathematics", "code": "BS(IT)409", "sem": 4,
        "credits": 3, "ltp": "3-0-0",
        "aliases": ["discrete mathematics", "discrete math", "discrete maths", "dm"],
        "topics": (
            "Number theory; counting and recurrence relations; propositional logic; "
            "algebraic structures and Boolean algebra; planar graphs and graph colouring."
        ),
    },
    {
        "name": "Design & Analysis of Algorithm", "code": "PC(IT)406", "sem": 4,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["design and analysis of algorithm", "daa", "analysis of algorithm"],
        "topics": (
            "Design paradigms (divide and conquer, greedy, dynamic programming, backtracking); "
            "sorting; graph algorithms; string matching; amortized analysis; P and NP."
        ),
    },
    {
        "name": "Formal Language and Automata Theory", "code": "PC(IT)407", "sem": 4,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["formal language and automata theory", "automata", "flat",
                    "toc", "theory of computation"],
        "topics": (
            "Finite automata and regular languages; context-free grammars and pushdown automata; "
            "context-sensitive languages; Turing machines; undecidability."
        ),
    },
    {
        "name": "Computer Architecture", "code": "PC(IT)408", "sem": 4,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["computer architecture", "coa"],
        "topics": (
            "Pipelining and hazards; memory modules; cache and virtual memory; "
            "instruction-level parallelism (RISC, VLIW); multiprocessors; VHDL and CAD tools."
        ),
    },
    {
        "name": "Biology for Engineers", "code": "ES(IT)411", "sem": 4,
        "credits": 3, "ltp": "3-0-0",
        "aliases": ["biology for engineers", "biology"],
        "topics": (
            "Cells and biomolecules; genetics; medical imaging; "
            "human physiology; biotechnology and synthetic biology."
        ),
    },
    {
        "name": "Constitution of India", "code": "HS(IT)406", "sem": 4,
        "credits": 2, "ltp": "2-0-0",
        "aliases": ["constitution of india", "constitution"],
        "topics": (
            "Indian Constitution basics; union and state executive; legal system; "
            "IPR and IT Act; business organizations and e-governance."
        ),
    },
    {
        "name": "Operating Systems", "code": "PC(IT)511", "sem": 5,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["operating system", "os"],
        "topics": (
            "Processes and threads; CPU scheduling, synchronization, deadlocks; "
            "memory management and virtual memory; file systems; "
            "disk and I/O management; protection and security."
        ),
    },
    {
        "name": "Database Management System", "code": "PC(IT)512", "sem": 5,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["database management system", "dbms", "database"],
        "topics": (
            "ER model; relational algebra and SQL; normalization; "
            "transactions and concurrency control; indexing and B+ trees."
        ),
    },
    {
        "name": "Object Oriented Programming", "code": "PC(IT)513", "sem": 5,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["object oriented programming", "oop", "java", "oops"],
        "topics": (
            "OOP concepts and Java basics; inheritance, polymorphism, "
            "abstract classes, interfaces, packages; exception handling; "
            "multithreading; applets."
        ),
    },
    {
        "name": "Artificial Intelligence", "code": "PC(IT)514", "sem": 5,
        "credits": 3, "ltp": "3-0-0",
        "aliases": ["artificial intelligence", "ai"],
        "topics": (
            "Intelligent agents; search techniques (BFS, A*, minimax); "
            "knowledge and reasoning; machine learning and planning; "
            "generative AI tools and applications."
        ),
    },
    {
        "name": "Computer Networks", "code": "PC(IT)601", "sem": 6,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["computer networks", "cn", "networking"],
        "topics": (
            "OSI and TCP/IP model; routing and switching algorithms; "
            "transport protocols (TCP, UDP); network security; "
            "wireless and cellular networking."
        ),
    },
    {
        "name": "Software Engineering", "code": "PC(IT)603", "sem": 6,
        "credits": 4, "ltp": "3-1-0",
        "aliases": ["software engineering", "se"],
        "topics": (
            "SDLC models (Agile, Waterfall, Spiral); requirements engineering; "
            "design patterns; testing strategies; project management; UML."
        ),
    },
    {
        "name": "Introduction to Cyber Security", "code": "PC(IT)604", "sem": 6,
        "credits": 3, "ltp": "3-0-0",
        "aliases": ["cyber security", "cybersecurity", "information security",
                    "intro to cyber security"],
        "topics": (
            "Cryptography; network security; ethical hacking basics; "
            "firewalls; intrusion detection; security protocols; cyber laws."
        ),
    },
]

# -----------------------------------------------------------------------
# TEXT PROCESSING UTILITIES
# -----------------------------------------------------------------------
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "am", "be", "of", "in",
    "on", "at", "to", "for", "me", "my", "please", "tell", "about", "can",
    "you", "i", "do", "does", "and", "or", "it", "there", "any", "give",
}


def stem(word: str) -> str:
    """Very light stemming: 'timings' -> 'timing', 'labs' -> 'lab'."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def stem_text(text: str) -> str:
    return " ".join(stem(w) for w in normalize(text).split())


# -----------------------------------------------------------------------
# KNOWLEDGE-BASE FAQ  (keyword + phrase scoring)
# -----------------------------------------------------------------------
FAQ = [
    {
        "topic": "Greeting",
        "keywords": {"hello", "hi", "hey", "namaste", "morning", "afternoon", "evening"},
        "phrases": ["good morning", "good afternoon", "good evening"],
        "answer": (
            "Hello! I'm the {short_name} {dept} Department assistant. "
            "Ask me anything about GCECT — subjects, fees, exams, placements, and more!"
        ),
    },
    {
        "topic": "Thanks",
        "keywords": {"thank", "thanks", "thankyou"},
        "phrases": ["thank you"],
        "answer": "You're welcome! Feel free to ask anything else about GCECT.",
    },
    {
        "topic": "About the college",
        "keywords": {"college", "institute", "name", "full", "city", "university",
                     "autonomous", "makaut", "affiliation", "gcect"},
        "phrases": ["full name", "college name", "which college", "about college", "about gcect"],
        "answer": (
            "{college_name} ({short_name}), {city}.\n"
            "{affiliation}.\n"
            "Address: {address}\n"
            "Website: {website}"
        ),
    },
    {
        "topic": "Head of Department (HOD)",
        "keywords": {"hod", "head", "cabin", "room", "who"},
        "phrases": ["head of department", "hod office", "hod room", "hod cabin"],
        "answer": (
            "HOD of {dept}: {hod_name}.\n"
            "Office: Room {hod_room}, Floor {hod_floor}, {building}."
        ),
    },
    {
        "topic": "Faculty",
        "keywords": {"faculty", "teacher", "professor", "staff", "lecturer", "teach"},
        "phrases": ["faculty list", "faculty members", "who teaches"],
        "answer": "View the {dept} faculty list here: {faculty_link}",
    },
    {
        "topic": "Department location",
        "keywords": {"where", "location", "located", "building", "floor",
                     "department", "dept", "find", "reach", "address"},
        "phrases": ["where is the department", "how to reach", "it department location"],
        "answer": (
            "The {dept} Department is on Floor {dept_floor} of the {building}, "
            "{college_name}.\nAddress: {address}"
        ),
    },
    {
        "topic": "Department timings",
        "keywords": {"department", "dept", "timing", "time", "hour", "open", "close"},
        "phrases": ["department timing", "office timing", "office hours"],
        "answer": "Department office hours: {dept_hours}.",
    },
    {
        "topic": "Library timings",
        "keywords": {"library", "book", "librarian", "timing", "time", "hour",
                     "open", "close"},
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
        "answer": (
            "Ask for a specific semester, e.g. '3rd semester subjects', "
            "'2nd year subjects', or a subject like 'operating systems topics'."
        ),
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
        "answer": "Semester examination schedule: {exam_link}",
    },
    {
        "topic": "Exam pattern and marks",
        "keywords": {"marks", "pattern", "internal", "mid", "assessment",
                     "grading", "credit", "pass"},
        "phrases": ["exam pattern", "mid sem", "mid semester", "end semester",
                    "internal marks"],
        "answer": (
            "Theory paper marks:\n"
            "  Internal (50): Mid-Sem 1 = 15, Mid-Sem 2 = 15, "
            "Assignments/Quiz/Attendance = 20\n"
            "  End Semester: 100 marks → converted to 50\n"
            "  Total: 100 marks\n\n"
            "Lab papers: Graded on attendance, lab report, experimental work, "
            "presentation, and viva."
        ),
    },
    {
        "topic": "Internship and training",
        "keywords": {"internship", "industrial", "training", "summer", "intern"},
        "phrases": ["summer internship", "industrial training"],
        "answer": (
            "Internship structure:\n"
            "  • After Sem 2: 2–4 weeks summer internship (evaluated in Sem 3)\n"
            "  • After Sem 4: 2–4 weeks summer internship (evaluated in Sem 5)\n"
            "  • After Sem 6: 4–6 weeks industrial training (evaluated in Sem 7)\n"
            "  • Sem 7 & 8: Project / Internship / Industrial Project"
        ),
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
        "answer": "Annual tuition fee (B.Tech IT): {fees}. Please confirm the latest details with the office.",
    },
    {
        "topic": "Scholarships",
        "keywords": {"scholarship", "freeship", "svmcm", "stipend", "financial", "aid"},
        "phrases": ["financial aid", "student freeship", "swami vivekananda"],
        "answer": "Scholarships and financial support: {scholarships}.",
    },
    {
        "topic": "Placement and training cell",
        "keywords": {"placement", "placed", "recruit", "company", "job",
                     "package", "tnp", "campus"},
        "phrases": ["training and placement", "placement cell", "campus placement"],
        "answer": "Training & Placement details for {dept}: {placement_link}",
    },
    {
        "topic": "Clubs and technical activities",
        "keywords": {"club", "fest", "technical", "bytemonk", "event",
                     "society", "activity", "coding", "hackathon"},
        "phrases": ["tech fest", "technical club", "coding club", "bytemonk club"],
        "answer": (
            "Technical club: {clubs}.\n"
            "Bytemonk organizes coding contests, workshops, hackathons, "
            "and tech events for IT students."
        ),
    },
    {
        "topic": "Hostel",
        "keywords": {"hostel", "accommodation", "stay", "mess", "boarding"},
        "phrases": ["hostel facility"],
        "answer": (
            "For hostel and accommodation details, please contact the college office "
            "directly or visit {website}."
        ),
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
        "phrases": ["contact number", "phone number", "email id", "email address"],
        "answer": "Department email: {email}\nDepartment phone: {phone}",
    },
    {
        "topic": "Course overview",
        "keywords": {"course", "btech", "program", "overview", "structure",
                     "semesters", "total"},
        "phrases": ["course structure", "btech it", "it program", "how many semesters"],
        "answer": (
            "B.Tech IT at {short_name} (Curriculum 2024-25 onwards) — 8 semesters / 4 years:\n"
            "  Sem 1-2: Foundation (Maths, Physics, Chemistry, Programming basics)\n"
            "  Sem 3-4: Core IT (DSA, CO, DAA, FLAT, Computer Architecture)\n"
            "  Sem 5-6: Advanced IT (OS, DBMS, OOP, AI, Networks, Cyber Security)\n"
            "  Sem 7-8: Electives, Industrial Training, Projects & Viva Voce\n"
            "Internships are mandatory after Sem 2, Sem 4, and Sem 6."
        ),
    },
]

# Stem keywords once
for _entry in FAQ:
    _entry["keywords"] = {stem(k) for k in _entry["keywords"]}

VOCAB = sorted({k for e in FAQ for k in e["keywords"]})


def correct_spelling(word: str) -> str:
    if word in VOCAB or len(word) < 4 or word.isdigit():
        return word
    match = difflib.get_close_matches(word, VOCAB, n=1, cutoff=0.8)
    return match[0] if match else word


def get_words(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    words = [stem(w) for w in words if w not in STOPWORDS]
    return {correct_spelling(w) for w in words}


# -----------------------------------------------------------------------
# SEMESTER & SUBJECT DETECTION
# -----------------------------------------------------------------------
ORDINALS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4,
    "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
}
NUM = r"(\d|first|second|third|fourth|fifth|sixth|seventh|eighth)"


def to_number(token: str) -> int:
    return int(token) if token.isdigit() else ORDINALS[token]


def extract_semesters(text: str) -> list:
    t = text.lower()
    m = (re.search(NUM + r"(?:st|nd|rd|th)?\s*(?:sem|semester)\b", t)
         or re.search(r"\b(?:sem|semester)\s*" + NUM + r"\b", t))
    if m:
        sem = to_number(m.group(1))
        return [sem] if 1 <= sem <= 8 else []
    m = re.search(NUM + r"(?:st|nd|rd|th)?\s*year\b", t)
    if m:
        year = to_number(m.group(1))
        if 1 <= year <= 4:
            return [2 * year - 1, 2 * year]
    return []


def format_semester(sem: int) -> str:
    data = SYLLABUS[sem]
    lines = [
        f"<strong>Semester {sem}</strong> ({data['credits']} credits)",
        f"Theory: {data['theory']}",
        f"Labs / Sessional: {data['lab']}",
    ]
    if data["note"]:
        lines.append(f"Note: {data['note']}")
    return "\n".join(lines)


def syllabus_answer(question: str):
    semesters = extract_semesters(question)
    if not semesters:
        return None
    return "\n\n".join(format_semester(s) for s in semesters)


def find_subject(question: str):
    """Return the SUBJECTS entry best matching the question (longest alias wins)."""
    stemmed = stem_text(question)
    best, best_len = None, 0
    for subject in SUBJECTS:
        for alias in subject["aliases"]:
            a = stem_text(alias)
            if len(a) > best_len and re.search(r"\b" + re.escape(a) + r"\b", stemmed):
                best, best_len = subject, len(a)
    return best


def subject_answer(subject: dict) -> str:
    return (
        f"<strong>{subject['name']}</strong> ({subject['code']}) — "
        f"Semester {subject['sem']}, {subject['credits']} credits "
        f"(L-T-P: {subject['ltp']}).\n"
        f"Topics: {subject['topics']}"
    )


# -----------------------------------------------------------------------
# ML CLASSIFIER  (TF-IDF + Logistic Regression on intents.json)
# -----------------------------------------------------------------------
with open("intents.json", "r", encoding="utf-8") as _f:
    _data = json.load(_f)

_sentences, _labels, _responses = [], [], {}
for _intent in _data["intents"]:
    _tag = _intent["tag"]
    _responses[_tag] = _intent["responses"]
    for _pattern in _intent["patterns"]:
        _sentences.append(_pattern)
        _labels.append(_tag)

_vectorizer = TfidfVectorizer()
_X = _vectorizer.fit_transform(_sentences)
_clf = LogisticRegression(max_iter=1000)
_clf.fit(_X, _labels)


def ml_response(question: str) -> str:
    """Return the ML-picked intent response."""
    vec = _vectorizer.transform([question])
    tag = _clf.predict(vec)[0]
    return random.choice(_responses[tag])


# -----------------------------------------------------------------------
# MATCHING ENGINE
# -----------------------------------------------------------------------
def score_entry(entry: dict, words: set, clean_text: str) -> int:
    score = len(words & entry["keywords"])
    score += 3 * sum(1 for p in entry["phrases"] if p in clean_text)
    return score


def render_answer(entry: dict) -> str:
    return entry["answer"].format(**INFO)


def kb_find_answer(question: str):
    """
    Try the local knowledge-base first.
    Returns (kind, payload):
      ("answer", text)      – clear best match
      ("none", None)        – nothing matched
    """
    # 1) Subject-level match (e.g. "DBMS topics")
    subject = find_subject(question)
    if subject:
        return "answer", subject_answer(subject)

    # 2) FAQ keyword/phrase scoring
    words = get_words(question)
    clean_text = normalize(question)
    scored = [(score_entry(e, words, clean_text), e) for e in FAQ]
    best = max(s for s, _ in scored)

    if best == 0:
        return "none", None

    winners = [e for s, e in scored if s == best]
    entry = winners[0]

    # 3) Detailed semester answer if syllabus topic triggered
    if entry["topic"] == "Syllabus and subjects":
        special = syllabus_answer(question)
        if special:
            return "answer", special

    return "answer", render_answer(entry)


# -----------------------------------------------------------------------
# FLASK APP
# -----------------------------------------------------------------------
app = Flask(__name__)


def get_response(question: str) -> str:
    kind, payload = kb_find_answer(question)
    if kind == "answer":
        return payload
    # Fall back to ML classifier
    return ml_response(question)


@app.route("/")
def intro():
    """Scroll-locked video hero — very first entry point."""
    return render_template("intro.html")


@app.route("/landing")
def landing():
    """Animated features landing page."""
    return render_template("landing.html")


@app.route("/chatbot")
def chatbot():
    """The full chat UI."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "").strip()
    if not message:
        return jsonify({"response": "Please type a question!"})
    answer = get_response(message)
    return jsonify({"response": answer})


if __name__ == "__main__":
    app.run(debug=True)

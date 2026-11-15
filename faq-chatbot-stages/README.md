# Stages 3 & 4 — NLP Preprocessing and TF-IDF Matching

These follow on from your Stage 1 (rule-based, `if/elif`) and Stage 2
(dictionary knowledge base) chatbots. Each file below is standalone —
run it directly, no other files needed.

## Stage 3 — `stage3_nlp_preprocessing.py`

**Problem it solves:** Stage 2 matched a keyword only if it was an exact
substring of the question. "library" matches "where is the library",
but not if the user says "when does it open" with no "library" word at all
in a follow-up, or phrases things in an unexpected way.

**What it adds:** a `preprocess()` function that lowercases the sentence,
splits it into words (tokenization), and throws away both punctuation and
"stopwords" — common words like *the, is, does, what* that carry no topic
meaning. The chatbot then compares the *set of remaining words* in the
question against the set of remaining words in each FAQ entry, and answers
with whichever entry shares the most words. That's a real improvement:
"where can I find the library" and "what are the library timings" now both
correctly hit the library entry, which plain substring matching in Stage 2
could not guarantee.

**Known limitation** (worth mentioning in your report): it still needs the
*exact same word form*. "exam" and "examination" are two different tokens
to this code, so a question about "examination" won't match a FAQ entry
keyed on "exam". Stage 4 works around this differently.

```bash
pip install nltk
python stage3_nlp_preprocessing.py
```

## Stage 4 — `stage4_tfidf_chatbot.py`

**Problem it solves:** Stage 3's fix still relies on exact word matches.
Real questions get asked in many different ways.

**What it adds:** instead of one keyword per topic, we store several real
example questions per topic (`questions[]` / `answers[]`). **TF-IDF**
converts every question — the stored ones and the user's new one — into a
vector of numbers that weighs distinctive words (like "library") higher
than filler words. **Cosine similarity** then finds which stored question
is numerically closest to what the user typed, and we return that
question's answer.

```
User Question -> Preprocessing -> TF-IDF -> Cosine Similarity
             -> Find Most Similar Stored Question -> Return its Answer
```

```bash
pip install scikit-learn
python stage4_tfidf_chatbot.py
```

Two details worth knowing (and worth mentioning if your evaluator asks
"why not just use TF-IDF for everything?"):

- **`stop_words="english"`** on the vectorizer matters a lot here. Without
  it, common words like "who", "is", "the" get counted too, and a totally
  unrelated question like "what is the capital of India" can accidentally
  score high against an FAQ entry just because they share "is" and "the".
- TF-IDF cosine similarity can still be thrown off by **short questions**:
  a stored question with only one matching word can score *higher* than a
  longer, more relevant one, because cosine similarity normalizes by
  sentence length. This — plus the exact-word-form issue from Stage 3 — is
  exactly why the later stages (intent classification with a real ML
  classifier, which I already built for you as the full FastAPI project)
  are more robust: they learn from many phrasings per topic instead of
  nearest-neighbor matching against single stored sentences.

## Where this fits with what you already have

You already have a full working Stages 5-8 implementation (intent
classification with Logistic Regression, FastAPI backend, web UI, Docker)
in the `college-chatbot` project from earlier. These two files are the
missing middle steps — useful on their own to demonstrate progressive
learning in a report or viva, even though the final deployed chatbot uses
the stronger approach from Stage 5 onward.

## Stage 5 — `intents.json`

**Problem it solves:** Stage 4 stored questions and answers as two parallel
lists (`questions[]` / `answers[]`) — easy to get out of sync, and no
natural place to store more than one response per topic.

**What it adds:** a proper structure used in real conversational systems —
each topic ("intent") has a `tag`, a list of example `patterns` (ways
someone might ask about it), and a list of possible `responses`. This is
just data, not code — but it's the data Stage 6's classifier learns from.

## Stage 6 — `stage6_train_classifier.py`

**Problem it solves:** Stage 4's TF-IDF approach finds the closest *stored*
question — it can't generalize to a phrasing that doesn't resemble anything
in its list. This stage trains an actual **classifier**: TF-IDF features
feed into **Logistic Regression**, which learns a general notion of what
words are associated with each intent, not just a lookup table.

```
User question -> TF-IDF features -> Logistic Regression -> predicted intent
```

```bash
pip install scikit-learn
python stage6_train_classifier.py
```

This stage deliberately stops at **printing the detected intent** — wiring
that intent to an actual answer is Stage 7, the natural next step once
you've shown the classifier works.

**Known limitation, and it's a real one I found while testing:** with only
31 example patterns across 8 intents, the classifier sometimes gets it
wrong on phrasing it hasn't seen — in my test run, "who heads this
department" was misclassified as `greeting` at only 0.18 confidence
(barely above the 1-in-8 random baseline of 0.125). This isn't a bug, it's
what a classifier trained on a handful of examples per class looks like.
The fix is exactly the "training loop" from before: more patterns per
intent. The full FastAPI project I built earlier already applies this fix
(204 patterns, tuned regularization, character n-grams) and gets it right.

## Stage 7 — `stage7_chatbot.py`

**Problem it solves:** Stage 6 could tell you *which* intent a question
belonged to, but that's not an answer a user can actually read.

**What it adds:** the exact same TF-IDF + Logistic Regression model as
Stage 6, but now the predicted intent is used to look up that intent's
`responses` list in `intents.json`, and one is picked at random and
printed. This is the "core" terminal chatbot — everything after this is
about how it's delivered, not how it thinks.

```bash
pip install scikit-learn
python stage7_chatbot.py
```

**Known limitation, confirmed by testing it:** I asked it "what is the
weather today" and it confidently answered with the exam schedule
response anyway. `model.predict()` always returns its single best guess,
however wrong — there's no "I don't know" here. That's intentional for
this stage (it matches what Stage 7 is meant to teach), but it's worth
naming as a gap if you're asked about it, and it's exactly what the fuller
FastAPI project (from earlier) fixes with a confidence threshold.

## Stage 8 — `stage8_app.py` + `templates/index.html` + `static/style.css`

**Problem it solves:** Stage 7 only runs in a terminal — not something you
can demo to someone without them having Python installed.

**What it adds:** the identical chatbot logic from Stage 7, wrapped in a
small **Flask** web app. The browser page posts the user's question to a
`/chat` endpoint as JSON; Flask predicts the intent, picks a response, and
sends it back as JSON; a few lines of JavaScript update the page — no
reload needed.

```
Browser (index.html)
   -> POST /chat  {"message": "..."}
   -> Flask route
   -> TF-IDF + Logistic Regression (same model as Stage 6/7)
   -> JSON response
   -> JavaScript updates the page
```

```bash
pip install flask scikit-learn
python stage8_app.py
```

Then open the address it prints — usually **http://127.0.0.1:5000**.

I ran this one end-to-end (not just read the code): started the server,
sent it real HTTP requests for "when does the library close" and "who is
the HOD", and both came back correctly through `/chat` as JSON, with the
homepage and stylesheet serving correctly too.

This completes the same 8-stage progression as the original project brief
you uploaded, with each stage's real limitations called out rather than
glossed over — and the fuller FastAPI/Docker version from earlier already
shows where you'd take it next (confidence thresholds, a richer dataset,
containerized deployment).


---

## Running Stage 8 — environment & startup notes

### Phone-number placeholder warning

> ⚠️ **Action required before demo:** `stage8_app.py` contains a placeholder
> phone number (`"phone": "XXXX-XXXXXX"`) in the `INFO` dict. Replace it with
> the real college contact number before sharing or presenting the chatbot, or
> questions like "what is the contact number?" will return the placeholder.

### Setting environment variables

**Enable debug mode** (auto-reload on code changes, full tracebacks in browser):

```bash
# Windows PowerShell
$env:FLASK_DEBUG = "1"
python stage8_app.py

# Windows Command Prompt
set FLASK_DEBUG=1
python stage8_app.py

# Linux / macOS
FLASK_DEBUG=1 python stage8_app.py
```

> ⚠️ **Never run with `FLASK_DEBUG=1` in production** — the interactive
> debugger allows arbitrary code execution on the server.

**Set a secret key** (required for session security in OOP Quiz / Mock Paper mode):

```bash
# Windows PowerShell
$env:FLASK_SECRET_KEY = "replace-with-a-long-random-string"
python stage8_app.py

# Windows Command Prompt
set FLASK_SECRET_KEY=replace-with-a-long-random-string
python stage8_app.py

# Linux / macOS
FLASK_SECRET_KEY="replace-with-a-long-random-string" python stage8_app.py
```

If `FLASK_SECRET_KEY` is not set, `stage8_app.py` falls back to a hard-coded
development key — fine for local testing, **not safe for a public deployment**.
Generate a secure value with:

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## OOP / Java Exam Preparation Mode

### Overview

The OOP Exam Preparation Mode turns the chatbot into an interactive study
companion for the **Object-Oriented Programming with Java** course
(**PC(IT)513**) offered at GCECT. When the mode is triggered the chatbot draws
from `oops_bank.json` — a curated question bank covering all six syllabus
modules — and can generate quizzes, full mock papers, topic-focused revision
sets, and step-by-step explanations. Progress within a session is tracked
so the chatbot can adapt difficulty based on how well the student is doing.

### How to trigger it

Type any of the following phrases (or anything similar) in the chat box:

| Example phrase | What it starts |
|---|---|
| `oops quiz` | 10-question adaptive quiz on a random topic |
| `java exam preparation` | Full mode-selection menu |
| `hard questions on multithreading` | Hard-level questions filtered to Module 5 |
| `mock paper java` | Full-length mock exam (Section A / B / C) |
| `important questions on inheritance` | High-priority 10-mark questions on Module 3 |
| `learn encapsulation` | Concept explanation + worked example |
| `revision exception handling` | Rapid-fire revision set for Module 4 |

The chatbot's intent detector (`detect_oops_intent()` in `oops_engine.py`)
matches keywords such as *oops*, *java*, *quiz*, *mock*, *multithreading*,
*inheritance*, *exception*, *thread*, etc. A message that only mentions
*oops* as an incidental word (e.g. "oops syllabus" asking about the college
timetable) is **not** hijacked into exam mode — the detector requires at least
one additional exam-context signal.

### Modes available

**Learn mode** presents a concept explanation followed by one or two worked
examples and a short follow-up question to check understanding. It is best
suited for topics the student is meeting for the first time or wants to
revisit before attempting quiz questions. The explanation is drawn from the
`explanation` and `exam_tip` fields of the question bank and supplemented with
inline Java code snippets where relevant.

**Quiz mode** delivers a configurable number of questions (default: 10, set via
`DEFAULT_QUIZ_SIZE` in `oops_engine.py`) drawn from the question bank, filtered
by topic and/or difficulty if specified. After each answer the chatbot gives
immediate feedback — correct/wrong, the right answer, and a one-line
explanation. At the end it shows a score summary and an adaptive recommendation
(see difficulty levels below).

**Mock Paper mode** generates a full-length simulated end-semester paper
structured as three sections: **Section A** (short / 2-mark MCQ and
true-or-false), **Section B** (5-mark difference and short-answer), and
**Section C** (10-mark long / program / debug questions). The paper is randomly
assembled from the bank on each invocation so no two mock papers are identical.
Students can attempt it question-by-question in chat or download the full paper
as plain text.

**Code Lab mode** selects only `code_output`, `debug`, and `program` question
types from the bank and presents them one at a time with the student's answer
compared against the expected output (whitespace-normalised). It is specifically
designed to build confidence with Java syntax and runtime behaviour before the
practical component of the exam.

**Revision mode** is a rapid-fire session: shorter questions only (MCQ and
true/false), timed to approximately 30 seconds per question, covering the topic
the student selects. It is intended as a last-minute run-through the night
before the exam and prioritises questions tagged as `important` in the bank.

### Difficulty levels

> ⚠️ **Assumption**: The mark distribution (2-mark / 5-mark / 10-mark per
> difficulty level) is an educated inference from the OOP course (PC(IT)513)
> exam scheme (Mid-Sem 15+15, Assignment/Quiz 20, End-Sem 100→50). The exact
> mark-per-question distribution has **NOT** been confirmed from an actual
> question paper. Tune the `DIFFICULTY_MARKS` dict in `oops_engine.py` once
> you have the real paper.

| Level | Marks | Typical question types | Exam section / style |
|---|---|---|---|
| **Easy** | 2 | MCQ, True/False | Section A — recall, definitions |
| **Medium** | 5 | Short answer, Difference, Code output | Section B — application, comparison |
| **Hard** | 10 | Long answer, Program, Debug | Section C — design, analysis, full programs |

### Syllabus coverage

| Module | Hours | Key topics |
|---|---|---|
| **1** — OOP Introduction | 2 | OOP concepts & features, OOP vs procedural, object-oriented modelling |
| **2** — Java & Classes | 10 | Java advantages, JDK/JRE/JVM/bytecode, data types, variables, operators, control statements, loops, arrays, constants, methods, method overloading, keyboard input, classes & objects, access specifiers, instance vs static, constructors, constructor overloading, static blocks, array of objects, `this` keyword, passing/returning objects, nested/inner classes, String methods, command-line args, garbage collection |
| **3** — Inheritance & Polymorphism | 10 | Inheritance types, super/sub classes, generalization/specialization, constructor order, `super` keyword, method overriding, `static` keyword, abstract classes & interfaces, `final` keyword, dynamic binding, interface inheritance, nested abstract classes/interfaces, packages |
| **4** — Exception Handling | 5 | Exception hierarchy, checked vs unchecked, `try`/`catch`, nested try, multiple catch, `throw`/`throws`, `finally`, user-defined exceptions |
| **5** — Multithreading | 6 | Thread concept, main/child threads, thread lifecycle, `Thread` class vs `Runnable`, priorities, synchronization, `wait`/`notify`/`notifyAll`, deadlock, deprecated `suspend`/`resume` |
| **6** — Applets *(deprecated)* | 3 | Applet basics, lifecycle, applet vs application, parameter passing, I/O in applets |

### How to add questions to the bank

Questions live in `oops_bank.json` as a top-level `"questions"` array.
Each entry must conform to this schema:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | Unique. Format: `M{module}{level_char}{3-digit-num}` e.g. `M2E001`. Level chars: `E`=easy, `M`=medium, `H`=hard. Bonus: `BNS001`. |
| `module` | int or `"bonus"` | ✅ | Syllabus module number (1–6) or `"bonus"` for off-syllabus. |
| `topic` | string | ✅ | Fine-grained topic label, e.g. `"Constructor Overloading"`. |
| `level` | string | ✅ | `"easy"` / `"medium"` / `"hard"` |
| `type` | string | ✅ | `mcq` \| `true_false` \| `short` \| `difference` \| `code_output` \| `debug` \| `program` \| `long` |
| `marks` | int | ✅ | 2 / 5 / 10 |
| `question` | string | ✅ | The question text. |
| `code` | string or `null` | ✅ | Java code block to display (for `code_output`, `debug`), or `null`. |
| `options` | object or `null` | ✅ | For MCQ: `{"A": "...", "B": "...", "C": "...", "D": "..."}`. `null` for other types. |
| `answer` | string | ✅ | For MCQ: `"A"`–`"D"`. For true/false: `"True"` or `"False"`. For code_output: exact console output. For others: model answer text. |
| `explanation` | string | ✅ | Why the answer is correct (shown after the student answers). |
| `keywords` | list of string | ✅ | 2–6 keywords used by the ML intent detector and partial-credit scorer. |
| `exam_tip` | string | ✅ | Short advice, e.g. `"For 5 marks: define (1), diagram (1), 3 examples (3)"`. |
| `source` | string | ✅ | Always `"syllabus"`. Never claim `"previous year question"`. |

**Example entry:**

```json
{
  "id": "M2E001",
  "module": 2,
  "topic": "JVM",
  "level": "easy",
  "type": "mcq",
  "marks": 2,
  "question": "What does JVM stand for and what is its primary role?",
  "code": null,
  "options": {
    "A": "Java Virtual Machine — executes Java bytecode on any platform",
    "B": "Java Verified Module — verifies class file integrity",
    "C": "Java Variable Manager — manages memory allocation",
    "D": "Java Version Manager — selects the correct JDK version"
  },
  "answer": "A",
  "explanation": "The JVM interprets or JIT-compiles Java bytecode into native machine code, enabling platform independence — the core of Java's 'write once, run anywhere' promise.",
  "keywords": ["jvm", "bytecode", "platform", "virtual machine"],
  "exam_tip": "2-mark answer: one-line definition + one-line role. Mention bytecode and platform independence.",
  "source": "syllabus"
}
```

**Rules to follow when adding questions:**

- All Java code must be **syntactically correct** and produce the **exact stated output**.
- For `code_output` type, the `answer` field must be the exact console output (normalized whitespace is acceptable).
- For `true_false`, answer must be exactly `"True"` or `"False"`.
- Deprecated items (applets, `Thread.suspend()`/`resume()`) must include `"(deprecated - for exam only)"` in the explanation.
- Use **Java 17** syntax.

### Validating the question bank

`validate_bank.py` checks the bank for schema errors, duplicate IDs, and
coverage gaps. Run it from the project directory:

```bash
# Basic validation (schema + ID uniqueness + coverage table)
python validate_bank.py

# Full validation including compiling and running all Java code snippets
# Requires JDK 17+ on PATH
python validate_bank.py --run-java
```

**Expected output (no errors):**

```
Loading oops_bank.json ... 180 questions found.

Coverage table:
Module | Easy | Medium | Hard | Total
-------|------|--------|------|------
1      |   10 |     10 |   10 |    30
2      |   10 |     10 |   10 |    30
3      |   10 |     10 |   10 |    30
4      |   10 |     10 |   10 |    30
5      |   10 |     10 |   10 |    30
6      |   10 |     10 |   10 |    30
-------|------|--------|------|------
Total  |   60 |     60 |   60 |   180

No schema errors found.
All IDs unique.
✅ Validation passed.
```

If `--run-java` is passed, each question with a `code` field is compiled with
`javac` and run with `java`; actual output is compared against the `answer`
field. Any mismatch is reported as an error and the script exits with code 1.

Exit code **0** = all checks passed. Exit code **1** = one or more errors found.

### Running tests

```bash
pytest test_oops.py -v
```

The test file mocks the question bank with an embedded 50-question fixture
(no file I/O required) and covers grading, session flow, adaptive difficulty,
and intent detection. All 12 test cases should pass on a clean install.

### Configuration

Three constants in `oops_engine.py` control the exam prep behaviour:

| Constant | Default | Purpose |
|---|---|---|
| `DIFFICULTY_MARKS` | `{"easy": 2, "medium": 5, "hard": 10}` | Maps difficulty level to marks. **Tune this once you have the real exam paper.** |
| `DEFAULT_QUIZ_SIZE` | `10` | Number of questions per quiz session (overridden if the user specifies a count). |
| `ML_CONFIDENCE_THRESHOLD` | `0.45` | Minimum confidence from the TF-IDF + LR classifier to accept an intent; below this the chatbot falls back to a clarifying question. |

### Known limitations / what was not verified

The following items are **assumptions or inferences** made during development;
they have **not** been verified against official documents or question papers:

1. **Mark distribution per difficulty level** — the 2/5/10-mark mapping is
   inferred from the PC(IT)513 exam structure (Mid-Sem 30, End-Sem 100→50)
   and is a reasonable estimate, but the per-question mark allocation has not
   been confirmed from an actual question paper.

2. **Module hour counts** — hours per module (2 / 10 / 10 / 5 / 6 / 3) are
   taken from the publicly available syllabus document. If the department
   has revised the syllabus, some topics may be redistributed.

3. **Applet questions** — Module 6 (Applets) is included because it appears
   in the syllabus, but Applets were removed from the Java SE standard in
   Java 11. It is unclear whether the exam still tests them in depth or only
   historically. All applet questions are marked `"(deprecated - for exam only)"`.

4. **Java code correctness** — all code snippets were written carefully and
   checked manually, but `validate_bank.py --run-java` has **not** been run
   against the full bank on a CI server. Run it yourself before the exam to
   catch any output discrepancies.

5. **"Important" question tagging** — questions tagged with high `exam_tip`
   weight are based on common OOP exam patterns, not on past GCECT papers
   (which are not publicly available).

6. **Thread.suspend() / Thread.resume()** — included in the bank for
   completeness (they appear in the syllabus), but these methods have been
   deprecated since Java 1.2. Any question on them in a real exam would be
   testing historical knowledge only.

7. **Partial-credit scoring for short/long answers** — the keyword-overlap
   algorithm is a heuristic. It awards marks proportional to how many
   `keywords` from the bank entry appear in the student's answer. This is
   not a semantic judge; a student can phrase a correct answer in an
   unexpected way and still score low.

8. **Phone-number placeholder** — `stage8_app.py` ships with a placeholder
   contact number. See the [startup notes](#running-stage-8--environment--startup-notes)
   above for the fix.

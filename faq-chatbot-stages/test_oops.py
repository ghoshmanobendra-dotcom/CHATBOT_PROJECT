"""
test_oops.py — pytest suite for OopsEngine (oops_engine.py)
Run: pytest test_oops.py -v

All tests use an in-memory question bank fixture (no file I/O).
"""
import copy
import pytest

# ---------------------------------------------------------------------------
# Fixture: 50 synthetic questions embedded directly (no file read)
# ---------------------------------------------------------------------------

def _make_mcq(qid, module, level, marks, correct_opt="A"):
    return {
        "id": qid,
        "module": module,
        "topic": "OOP Concepts",
        "level": level,
        "type": "mcq",
        "marks": marks,
        "question": f"MCQ question {qid}?",
        "code": None,
        "options": {"A": "Alpha", "B": "Beta", "C": "Gamma", "D": "Delta"},
        "answer": correct_opt,
        "explanation": f"Explanation for {qid}.",
        "keywords": ["encapsulation", "object", "class"],
        "exam_tip": "Define, illustrate, example.",
        "source": "syllabus",
    }


def _make_tf(qid, module, level, marks, answer="True"):
    return {
        "id": qid,
        "module": module,
        "topic": "Inheritance",
        "level": level,
        "type": "true_false",
        "marks": marks,
        "question": f"True/False question {qid}?",
        "code": None,
        "options": None,
        "answer": answer,
        "explanation": f"Explanation for {qid}.",
        "keywords": ["inheritance", "super"],
        "exam_tip": "Think parent→child.",
        "source": "syllabus",
    }


def _make_short(qid, module, level, marks, keywords=None):
    kw = keywords or ["polymorphism", "method", "overriding", "dynamic", "binding"]
    return {
        "id": qid,
        "module": module,
        "topic": "Polymorphism",
        "level": level,
        "type": "short",
        "marks": marks,
        "question": f"Short answer question {qid}?",
        "code": None,
        "options": None,
        "answer": "Polymorphism allows one interface, multiple implementations.",
        "explanation": f"Explanation for {qid}.",
        "keywords": kw,
        "exam_tip": "Cover definition + example.",
        "source": "syllabus",
    }


def _make_code_output(qid, module, level, marks, code, answer):
    return {
        "id": qid,
        "module": module,
        "topic": "Code Output",
        "level": level,
        "type": "code_output",
        "marks": marks,
        "question": f"What is the output of this code?",
        "code": code,
        "options": None,
        "answer": answer,
        "explanation": f"Explanation for {qid}.",
        "keywords": ["output", "execution"],
        "exam_tip": "Trace line by line.",
        "source": "syllabus",
    }


def _make_long(qid, module, level, marks, keywords=None):
    kw = keywords or ["thread", "synchronization", "monitor", "deadlock", "wait", "notify"]
    return {
        "id": qid,
        "module": module,
        "topic": "Multithreading",
        "level": level,
        "type": "long",
        "marks": marks,
        "question": f"Long answer question {qid}?",
        "code": None,
        "options": None,
        "answer": "Detailed answer about multithreading concepts.",
        "explanation": f"Explanation for {qid}.",
        "keywords": kw,
        "exam_tip": "Cover lifecycle + diagram.",
        "source": "syllabus",
    }


@pytest.fixture(scope="session")
def sample_bank():
    """
    50 synthetic questions: 10 each across modules 1-5,
    varied types and levels, good enough for all test scenarios.
    """
    questions = []

    # Module 1 — 10 questions: 4 MCQ easy, 3 TF easy, 2 short medium, 1 long hard
    for i in range(1, 5):
        questions.append(_make_mcq(f"M1E{i:03d}", 1, "easy", 2, "A"))
    for i in range(1, 4):
        questions.append(_make_tf(f"M1E{4+i:03d}", 1, "easy", 2, "True"))
    for i in range(1, 3):
        questions.append(_make_short(f"M1M{i:03d}", 1, "medium", 5))
    questions.append(_make_long("M1H001", 1, "hard", 10))

    # Module 2 — 10 questions: 5 MCQ, 3 short, 2 code_output
    for i in range(1, 6):
        opt = ["A", "B", "C", "D", "A"][i - 1]
        questions.append(_make_mcq(f"M2E{i:03d}", 2, "easy", 2, opt))
    for i in range(1, 4):
        questions.append(_make_short(f"M2M{i:03d}", 2, "medium", 5))
    questions.append(_make_code_output(
        "M2H001", 2, "hard", 2,
        "public class A { public static void main(String[] a) { System.out.println(1 + 2); } }",
        "3",
    ))
    questions.append(_make_code_output(
        "M2H002", 2, "hard", 2,
        "public class B { public static void main(String[] a) { System.out.println(\"hello\"); } }",
        "hello",
    ))

    # Module 3 — 10 questions: mixed
    for i in range(1, 4):
        questions.append(_make_mcq(f"M3E{i:03d}", 3, "easy", 2, "B"))
    for i in range(1, 4):
        questions.append(_make_tf(f"M3M{i:03d}", 3, "medium", 5, "False"))
    for i in range(1, 3):
        questions.append(_make_short(f"M3M{3+i:03d}", 3, "medium", 5))
    for i in range(1, 3):
        questions.append(_make_long(f"M3H{i:03d}", 3, "hard", 10))

    # Module 4 — 10 questions
    for i in range(1, 6):
        questions.append(_make_mcq(f"M4E{i:03d}", 4, "easy", 2, "C"))
    for i in range(1, 4):
        questions.append(_make_short(f"M4M{i:03d}", 4, "medium", 5))
    for i in range(1, 3):
        questions.append(_make_long(f"M4H{i:03d}", 4, "hard", 10))

    # Module 5 — 10 questions (multithreading — used for mock paper + hard tests)
    for i in range(1, 4):
        questions.append(_make_mcq(f"M5E{i:03d}", 5, "easy", 2, "D"))
    for i in range(1, 4):
        questions.append(
            _make_short(f"M5M{i:03d}", 5, "medium", 5,
                        keywords=["thread", "runnable", "synchronization", "deadlock", "wait"])
        )
    for i in range(1, 5):
        questions.append(_make_long(f"M5H{i:03d}", 5, "hard", 10))

    assert len(questions) == 50, f"Expected 50, got {len(questions)}"
    return {"questions": questions}


# ---------------------------------------------------------------------------
# Helper: build an OopsEngine with the fixture bank
# ---------------------------------------------------------------------------

@pytest.fixture()
def engine(sample_bank):
    """Fresh OopsEngine instance with the in-memory fixture bank."""
    from oops_engine import OopsEngine
    eng = OopsEngine.__new__(OopsEngine)
    eng.__init__(bank=sample_bank)          # pass bank dict directly
    return eng


# ---------------------------------------------------------------------------
# 1. test_grade_mcq_correct
# ---------------------------------------------------------------------------

def test_grade_mcq_correct(engine):
    q = next(q for q in engine.bank if q["type"] == "mcq")
    result = engine.grade_answer(q, q["answer"])
    assert result["correct"] is True
    assert result["score"] == q["marks"]


# ---------------------------------------------------------------------------
# 2. test_grade_mcq_wrong
# ---------------------------------------------------------------------------

def test_grade_mcq_wrong(engine):
    q = next(q for q in engine.bank if q["type"] == "mcq")
    # Pick a wrong option (any key that is NOT the answer)
    wrong = next(k for k in ("A", "B", "C", "D") if k != q["answer"])
    result = engine.grade_answer(q, wrong)
    assert result["correct"] is False
    assert result["score"] == 0


# ---------------------------------------------------------------------------
# 3. test_grade_true_false
# ---------------------------------------------------------------------------

def test_grade_true_false(engine):
    q = next(q for q in engine.bank if q["type"] == "true_false")
    # Correct
    r_correct = engine.grade_answer(q, q["answer"])
    assert r_correct["correct"] is True
    assert r_correct["score"] == q["marks"]
    # Wrong
    wrong_ans = "False" if q["answer"] == "True" else "True"
    r_wrong = engine.grade_answer(q, wrong_ans)
    assert r_wrong["correct"] is False
    assert r_wrong["score"] == 0


# ---------------------------------------------------------------------------
# 4. test_grade_code_output_normalized
# ---------------------------------------------------------------------------

def test_grade_code_output_normalized(engine):
    q = next(q for q in engine.bank if q["type"] == "code_output")
    # Exact answer with extra whitespace should still match
    padded_answer = "  " + q["answer"] + "  \n"
    result = engine.grade_answer(q, padded_answer)
    assert result["correct"] is True


# ---------------------------------------------------------------------------
# 5. test_grade_short_partial_keywords
# ---------------------------------------------------------------------------

def test_grade_short_partial_keywords(engine):
    q = next(q for q in engine.bank if q["type"] == "short")
    keywords = q["keywords"]
    half = max(1, len(keywords) // 2)
    # Answer contains only half the keywords
    partial_answer = " ".join(keywords[:half]) + " some filler text"
    result = engine.grade_answer(q, partial_answer)
    assert result["score"] < q["marks"]
    assert result["score"] >= 0
    # partial — not fully correct (unless 50% threshold == full marks, which shouldn't happen)
    assert result["correct"] is False or result["score"] < q["marks"]


# ---------------------------------------------------------------------------
# 6. test_grade_short_all_keywords
# ---------------------------------------------------------------------------

def test_grade_short_all_keywords(engine):
    q = next(q for q in engine.bank if q["type"] == "short")
    all_kw_answer = " ".join(q["keywords"]) + " additional explanation here."
    result = engine.grade_answer(q, all_kw_answer)
    # All keywords present → near-full or full score
    assert result["score"] >= q["marks"] * 0.8
    assert result["correct"] is True


# ---------------------------------------------------------------------------
# 7. test_quiz_session_flow
# ---------------------------------------------------------------------------

def test_quiz_session_flow(engine):
    session = engine.start_quiz(module=None, level="easy", num_questions=3)
    assert session["state"] == "in_progress"
    assert len(session["questions"]) == 3
    assert session["current_index"] == 0
    assert session["score"] == 0

    for i in range(3):
        q = session["questions"][i]
        # Feed correct answer each time
        if q["type"] == "mcq":
            ans = q["answer"]
        elif q["type"] == "true_false":
            ans = q["answer"]
        else:
            ans = " ".join(q["keywords"])

        result = engine.submit_answer(session, ans)
        if i < 2:
            assert result["state"] == "in_progress"
            assert session["current_index"] == i + 1
        else:
            assert result["state"] == "complete"


# ---------------------------------------------------------------------------
# 8. test_adaptive_streak_up
# ---------------------------------------------------------------------------

def test_adaptive_streak_up(engine):
    """Two consecutive correct answers should trigger a 'try harder' recommendation."""
    session = engine.start_quiz(module=None, level="easy", num_questions=5)
    for _ in range(2):
        q = session["questions"][session["current_index"]]
        ans = q["answer"] if q["type"] in ("mcq", "true_false") else " ".join(q["keywords"])
        engine.submit_answer(session, ans)

    recommendation = engine.get_adaptive_recommendation(session)
    assert recommendation is not None
    # Should suggest trying a harder level or indicate good streak
    assert any(word in recommendation.lower() for word in
               ("harder", "higher", "medium", "great", "excellent", "try"))


# ---------------------------------------------------------------------------
# 9. test_adaptive_streak_down
# ---------------------------------------------------------------------------

def test_adaptive_streak_down(engine):
    """Two consecutive wrong answers should trigger a revision recommendation."""
    session = engine.start_quiz(module=None, level="easy", num_questions=5)
    for _ in range(2):
        q = session["questions"][session["current_index"]]
        # Deliberately wrong
        if q["type"] == "mcq":
            ans = next(k for k in ("A", "B", "C", "D") if k != q["answer"])
        elif q["type"] == "true_false":
            ans = "False" if q["answer"] == "True" else "True"
        else:
            ans = "completely wrong answer xyz"
        engine.submit_answer(session, ans)

    recommendation = engine.get_adaptive_recommendation(session)
    assert recommendation is not None
    assert any(word in recommendation.lower() for word in
               ("revise", "review", "revisit", "easier", "basic", "try again"))


# ---------------------------------------------------------------------------
# 10. test_oops_intent_detection
# ---------------------------------------------------------------------------

def test_oops_intent_detection(engine):
    from oops_engine import detect_oops_intent

    positive_cases = [
        "oops quiz",
        "start OOP exam",
        "java quiz mode",
        "hard questions on multithreading",
        "mock paper java",
        "give me an oop practice test",
        "test me on inheritance",
        "quiz on exception handling",
    ]
    for msg in positive_cases:
        result = detect_oops_intent(msg)
        assert result is not None, f"Expected intent detected for: {msg!r}"
        assert result.get("mode") in ("quiz", "mock", "revision", "hard"), \
            f"Unexpected mode {result.get('mode')!r} for: {msg!r}"


# ---------------------------------------------------------------------------
# 11. test_non_oops_intent_not_hijacked
# ---------------------------------------------------------------------------

def test_non_oops_intent_not_hijacked(engine):
    from oops_engine import detect_oops_intent

    # "oops syllabus" is asking about syllabus info, NOT triggering quiz mode
    negative_cases = [
        "oops syllabus",
        "what is oops",
        "explain oops concepts",
        "who is the HOD",
        "fees structure",
        "placement details",
        "5th semester subjects",
    ]
    for msg in negative_cases:
        result = detect_oops_intent(msg)
        assert result is None, \
            f"Expected NO intent for {msg!r}, but got: {result}"


# ---------------------------------------------------------------------------
# 12. test_mock_paper_structure
# ---------------------------------------------------------------------------

def test_mock_paper_structure(engine):
    paper = engine.generate_mock_paper()

    assert "section_a" in paper, "Mock paper must have section_a"
    assert "section_b" in paper, "Mock paper must have section_b"
    assert "section_c" in paper, "Mock paper must have section_c"

    # section_a: short / 2-mark questions
    for q in paper["section_a"]:
        assert q.get("marks") == 2 or q.get("type") in ("mcq", "true_false", "short"), \
            f"section_a question has unexpected type/marks: {q}"

    # section_b: medium / 5-mark questions
    for q in paper["section_b"]:
        assert q.get("marks") == 5 or q.get("type") in ("short", "difference"), \
            f"section_b question has unexpected type/marks: {q}"

    # section_c: long / 10-mark questions
    for q in paper["section_c"]:
        assert q.get("marks") == 10 or q.get("type") in ("long", "program", "debug"), \
            f"section_c question has unexpected type/marks: {q}"

    # Must have at least 1 question per section
    assert len(paper["section_a"]) >= 1
    assert len(paper["section_b"]) >= 1
    assert len(paper["section_c"]) >= 1

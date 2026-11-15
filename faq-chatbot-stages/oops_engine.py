"""
oops_engine.py — OOP Exam Prep Engine for GCECT Chatbot
=========================================================
Handles question bank loading, grading (MCQ/code/text), quiz sessions,
adaptive difficulty, mock paper generation, and revision notes.
"""

import json
import math
import random
import re
import os
from datetime import datetime
from collections import defaultdict

# =========================================================
# GRADING CONSTANTS
# =========================================================
DIFFICULTY_MARKS = {
    "easy":   2,   # 2-mark questions
    "medium": 5,   # 5-mark questions
    "hard":   10,  # 10-mark questions
}
DEFAULT_QUIZ_SIZE = 10
ADAPTIVE_STREAK_UP   = 2   # correct streak to offer next level
ADAPTIVE_STREAK_DOWN = 2   # wrong streak to offer easier + revision note
TFIDF_SIMILARITY_WEIGHT  = 0.2   # weight for cosine sim in grading
KEYWORD_COVERAGE_WEIGHT  = 0.8   # weight for keyword coverage in grading

LEVELS = ["easy", "medium", "hard"]


# =========================================================
# TF-IDF UTILITIES  (lightweight, no sklearn needed)
# =========================================================

def _tokenize(text: str) -> list:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tf(tokens: list) -> dict:
    freq = defaultdict(int)
    for t in tokens:
        freq[t] += 1
    n = len(tokens) or 1
    return {t: c / n for t, c in freq.items()}


def _idf(documents: list) -> dict:
    N = len(documents)
    df = defaultdict(int)
    for doc in documents:
        for t in set(doc):
            df[t] += 1
    return {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}


def _tfidf_vec(tokens: list, idf_map: dict) -> dict:
    tf = _tf(tokens)
    return {t: tf[t] * idf_map.get(t, 1.0) for t in tf}


def _cosine(v1: dict, v2: dict) -> float:
    dot = sum(v1.get(t, 0) * v2.get(t, 0) for t in v2)
    n1 = math.sqrt(sum(x * x for x in v1.values()))
    n2 = math.sqrt(sum(x * x for x in v2.values()))
    if not n1 or not n2:
        return 0.0
    return dot / (n1 * n2)


def _keyword_coverage(user_tokens: set, keywords: list) -> float:
    if not keywords:
        return 1.0
    kw_tokens = {t for k in keywords for t in _tokenize(k)}
    hit = kw_tokens & user_tokens
    return len(hit) / len(kw_tokens) if kw_tokens else 0.0


# =========================================================
# OOP INTENT DETECTION UTILITIES
# =========================================================
OOP_INTENT_KEYWORDS = {
    "quiz", "quizz", "practice", "question", "questions", "important",
    "prepare", "preparation", "mock", "test", "exam", "revise", "revision",
    "learn", "study", "hard", "easy", "medium", "topic", "topics",
}
OOP_SUBJECT_KEYWORDS = {
    "java", "oop", "oops", "object", "oriented", "inheritance",
    "polymorphism", "encapsulation", "abstraction", "interface", "abstract",
    "exception", "thread", "multithreading", "applet", "class", "method",
    "overload", "override", "constructor", "package", "extends", "implements",
}

TOPIC_TO_MODULE = {
    "multithreading": 5, "thread": 5,
    "inheritance": 3, "polymorphism": 3, "interface": 3, "abstract": 3, "package": 3,
    "exception": 4, "try": 4, "catch": 4,
    "applet": 6,
    "class": 2, "object": 2, "constructor": 2, "overload": 2, "array": 2,
    "oop": 1, "oops": 1, "encapsulation": 1, "abstraction": 1,
}

def detect_oops_intent(message: str) -> dict | None:
    """
    Detect if message is an OOP preparation request.
    Returns dict with keys 'mode', 'level', 'module' or None if not an OOP prep request.
    """
    lowered = message.lower()
    # Explicit exclusions: information-seeking queries
    if re.search(r"\b(oop|oops|java)\s+(syllabus|topics?|credit|credits|hours?)\b", lowered):
        return None
    if re.search(r"^(what\s+is\s+oops?|explain\s+oops?\s+concepts|who\s+is|fees|placement|\d+(st|nd|rd|th)?\s*semester\s+subjects)", lowered):
        return None

    words = set(re.findall(r"[a-z]+", lowered))
    has_oop_subject = bool(words & OOP_SUBJECT_KEYWORDS)
    has_intent = bool(words & OOP_INTENT_KEYWORDS)

    patterns = [
        r"\boops?\s+(quiz|practice|exam|test|mock|question|prep)",
        r"\bjava\s+(quiz|practice|exam|test|mock|question|prep)",
        r"\b(quiz|practice|mock|test)\s+on\s+\w+",
        r"\b(hard|easy|medium)\s+questions?\s+on\s+\w+",
        r"\bimportant\s+questions?\s+(on|for|about)\s+\w+",
        r"\bstart\s+oop\s+exam\b",
        r"\btest\s+me\s+on\s+\w+",
    ]
    matched_pattern = any(re.search(p, lowered) for p in patterns)

    if (has_oop_subject and has_intent) or matched_pattern:
        mode = "quiz"
        if "mock" in lowered:
            mode = "mock"
        elif "revision" in lowered or "revise" in lowered or "important" in lowered:
            mode = "revision"
        elif "hard" in lowered:
            mode = "hard"

        level = None
        for lvl in ("hard", "medium", "easy"):
            if lvl in lowered:
                level = lvl
                break

        module = None
        for kw, mod in TOPIC_TO_MODULE.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", lowered):
                module = mod
                break

        return {"mode": mode, "level": level, "module": module}
    return None

class OopsEngine:
    """
    Core engine for OOP exam prep quizzes.

    Parameters
    ----------
    bank_path : str | None
        Absolute path to oops_bank.json
    bank : dict | list | None
        In-memory bank dictionary or list of questions (for testing)
    """

    def __init__(self, bank_path: str = None, bank = None):
        if bank is not None:
            if isinstance(bank, dict):
                self.bank = bank.get("questions", [])
            elif isinstance(bank, list):
                self.bank = bank
            else:
                self.bank = []
        elif bank_path is not None:
            with open(bank_path, encoding="utf-8") as f:
                raw = json.load(f)
            self.bank: list = raw.get("questions", [])
        else:
            self.bank = []

        # Pre-build IDF from all model answers for grading
        docs = []
        for q in self.bank:
            answer_text = q.get("answer", "")
            if isinstance(answer_text, str):
                docs.append(_tokenize(answer_text))
        self._idf = _idf(docs) if docs else {}

    # ----------------------------------------------------------
    # FILTERING
    # ----------------------------------------------------------

    def filter_questions(
        self,
        module=None,
        level=None,
        types=None,
        important_only=False,
        exclude_ids=None,
    ) -> list:
        """
        Filter bank by module, level, types, important flag.

        Parameters
        ----------
        module : int | None
            OOP module number (1-6). None = all.
        level : str | None
            "easy" | "medium" | "hard" | None = all.
        types : list[str] | None
            e.g. ["mcq", "true_false"]. None = all.
        important_only : bool
            If True, only questions with "important": True.
        exclude_ids : set | None
            Question IDs to skip.

        Returns
        -------
        list of question dicts
        """
        exclude_ids = exclude_ids or set()
        result = []
        for q in self.bank:
            if q.get("id") in exclude_ids:
                continue
            if module is not None and q.get("module") != module:
                continue
            if level is not None and q.get("level") != level:
                continue
            if types is not None and q.get("type") not in types:
                continue
            if important_only and not q.get("important", False):
                continue
            result.append(q)
        return result

    # ----------------------------------------------------------
    # GRADING
    # ----------------------------------------------------------

    def grade_answer(self, question: dict, user_answer: str) -> dict:
        """
        Grade user_answer against question.

        Returns
        -------
        dict with keys: correct, score, max_marks, pct,
                        missing_keywords, model_answer, explanation, feedback
        """
        qtype = question.get("type", "short")
        marks = question.get("marks", DIFFICULTY_MARKS.get(question.get("level", "easy"), 2))
        model_ans = str(question.get("answer", ""))
        explanation = question.get("explanation", "")
        keywords: list = question.get("keywords", [])

        user_norm = user_answer.strip().lower()
        model_norm = model_ans.strip().lower()

        # ---- Exact-match types ----
        if qtype in ("mcq", "true_false"):
            correct = user_norm == model_norm
            score = marks if correct else 0
            feedback = (
                f"✅ Correct! {explanation}"
                if correct
                else f"❌ Incorrect. Answer: **{model_ans}**. {explanation}"
            )
            return {
                "correct": correct,
                "score": score,
                "max_marks": marks,
                "pct": 100.0 if correct else 0.0,
                "missing_keywords": [],
                "model_answer": model_ans,
                "explanation": explanation,
                "feedback": feedback,
            }

        # ---- Code output: normalize whitespace ----
        if qtype == "code_output":
            u = re.sub(r"\s+", " ", user_norm).strip()
            m = re.sub(r"\s+", " ", model_norm).strip()
            correct = u == m
            score = marks if correct else 0
            feedback = (
                f"✅ Correct output! {explanation}"
                if correct
                else (
                    f"❌ Expected output:\n```\n{model_ans}\n```\n"
                    f"Your answer: `{user_answer.strip()}`\n{explanation}"
                )
            )
            return {
                "correct": correct,
                "score": score,
                "max_marks": marks,
                "pct": 100.0 if correct else 0.0,
                "missing_keywords": [],
                "model_answer": model_ans,
                "explanation": explanation,
                "feedback": feedback,
            }

        # ---- Text types: TF-IDF cosine + keyword coverage ----
        user_tokens = _tokenize(user_answer)
        model_tokens = _tokenize(model_ans)

        user_vec = _tfidf_vec(user_tokens, self._idf)
        model_vec = _tfidf_vec(model_tokens, self._idf)

        cosine_sim = _cosine(user_vec, model_vec)
        kw_cov = _keyword_coverage(set(user_tokens), keywords)

        raw_pct = (
            TFIDF_SIMILARITY_WEIGHT  * cosine_sim
            + KEYWORD_COVERAGE_WEIGHT * kw_cov
        )
        # Clamp to [0, 1]
        raw_pct = min(1.0, max(0.0, raw_pct))
        score = round(raw_pct * marks, 1)
        correct = raw_pct >= 0.6

        # Missing keywords
        user_token_set = set(user_tokens)
        missing = [
            kw for kw in keywords
            if not any(t in user_token_set for t in _tokenize(kw))
        ]

        if correct:
            feedback = f"✅ Good answer! Score: {score}/{marks}."
            if missing:
                feedback += f" You could also mention: {', '.join(missing[:3])}."
        else:
            feedback = (
                f"❌ Partial/incorrect. Score: {score}/{marks}.\n"
                f"Key points missing: {', '.join(missing[:5]) if missing else 'review model answer'}.\n"
                f"**Model Answer:** {model_ans}"
            )
        if explanation:
            feedback += f"\n💡 {explanation}"

        return {
            "correct": correct,
            "score": float(score),
            "max_marks": marks,
            "pct": round(raw_pct * 100, 1),
            "missing_keywords": missing,
            "model_answer": model_ans,
            "explanation": explanation,
            "feedback": feedback,
        }

    # ----------------------------------------------------------
    # QUIZ SESSION MANAGEMENT
    # ----------------------------------------------------------

    def _get_q_by_id(self, qid: str) -> dict | None:
        """Helper to get question by ID from bank."""
        for q in self.bank:
            if q.get("id") == qid:
                return q
        return None

    def start_quiz(
        self,
        module=None,
        level: str = "easy",
        n: int = DEFAULT_QUIZ_SIZE,
        num_questions: int = None,
        types=None,
    ) -> dict:
        """
        Sample n questions and return initial session state.

        Returns
        -------
        dict: session state (store in Flask session)
        """
        if num_questions is not None:
            n = num_questions
        pool = self.filter_questions(module=module, level=level, types=types)
        if not pool:
            # Fallback: ignore level
            pool = self.filter_questions(module=module, types=types)
        if not pool:
            pool = list(self.bank)

        random.shuffle(pool)
        selected = pool[:n]
        selected_ids = [q["id"] for q in selected]

        # Store compact question objects in session so callers/tests can inspect q['type'], etc.
        compact_qs = [
            {
                "id": q.get("id"),
                "type": q.get("type"),
                "answer": q.get("answer"),
                "keywords": q.get("keywords", []),
                "marks": q.get("marks", DIFFICULTY_MARKS.get(q.get("level", "easy"), 2)),
                "topic": q.get("topic", "")
            }
            for q in selected
        ]

        return {
            "state": "in_progress",
            "current_index": 0,
            "questions": compact_qs,
            "q_ids": selected_ids,
            "current_idx": 0,
            "total": len(selected_ids),
            "score": 0.0,
            "max_score": sum(
                q.get("marks", DIFFICULTY_MARKS.get(q.get("level", "easy"), 2))
                for q in selected
            ),
            "correct_streak": 0,
            "wrong_streak": 0,
            "current_level": level,
            "module": module,
            "answered": [],         # list of {id, correct, score, topic}
            "weak_topics": [],
        }

    def next_question(self, session: dict) -> dict:
        """
        Return next question payload for the client.

        Returns
        -------
        dict with type="quiz_question" or type="summary" if done.
        """
        idx = session.get("current_idx", 0)
        q_ids = session.get("q_ids") or session.get("questions", [])

        if idx >= len(q_ids):
            return self._build_summary(session)

        item = q_ids[idx]
        q = item if isinstance(item, dict) else self._get_q_by_id(item)
        if not q:
            return self._build_summary(session)

        payload = {
            "type": "quiz_question",
            "id": q.get("id"),
            "question_no": idx + 1,
            "total": session["total"],
            "question": q.get("question", ""),
            "text": q.get("question", ""),
            "code": q.get("code"),
            "qtype": q.get("type"),
            "marks": q.get("marks", DIFFICULTY_MARKS.get(q.get("level", "easy"), 2)),
            "options": q.get("options"),
            "topic": q.get("topic", ""),
            "exam_tip": q.get("exam_tip", ""),
            "level": q.get("level", ""),
        }
        return payload

    def submit_answer(self, session: dict, user_answer: str) -> dict:
        """
        Grade the current question, update session, check adaptive thresholds.

        Returns
        -------
        dict: feedback payload (type="feedback") with optional adaptive hint.
        """
        idx = session.get("current_idx", 0)
        q_ids = session.get("q_ids") or session.get("questions", [])

        if idx >= len(q_ids):
            return {"type": "error", "text": "Quiz already finished."}

        item = q_ids[idx]
        q = item if isinstance(item, dict) else self._get_q_by_id(item)
        if not q:
            return {"type": "error", "text": "Question not found."}

        result = self.grade_answer(q, user_answer)

        # Update session
        session["score"] += result["score"]
        if result["correct"]:
            session["correct_streak"] += 1
            session["wrong_streak"] = 0
        else:
            session["wrong_streak"] += 1
            session["correct_streak"] = 0
            topic = q.get("topic", "")
            if topic and topic not in session["weak_topics"]:
                session["weak_topics"].append(topic)

        session["answered"].append({
            "id": q.get("id"),
            "correct": result["correct"],
            "score": result["score"],
            "topic": q.get("topic", ""),
        })
        session["current_idx"] = idx + 1
        session["current_index"] = idx + 1
        is_complete = session["current_idx"] >= session["total"]
        session["state"] = "complete" if is_complete else "in_progress"

        # Adaptive hints
        adaptive_hint = None
        cur_level = session.get("current_level", "easy")
        if result["correct"] and session["correct_streak"] >= ADAPTIVE_STREAK_UP:
            next_level_idx = LEVELS.index(cur_level) + 1 if cur_level in LEVELS else -1
            if next_level_idx < len(LEVELS):
                next_level = LEVELS[next_level_idx]
                adaptive_hint = {
                    "type": "level_up",
                    "text": f"🔥 Great streak! Ready for **{next_level}** questions?",
                    "suggested_level": next_level,
                }
        elif not result["correct"] and session["wrong_streak"] >= ADAPTIVE_STREAK_DOWN:
            prev_level_idx = LEVELS.index(cur_level) - 1 if cur_level in LEVELS else -1
            if prev_level_idx >= 0:
                prev_level = LEVELS[prev_level_idx]
                adaptive_hint = {
                    "type": "level_down",
                    "text": (
                        f"💪 Don't give up! Try some **{prev_level}** questions "
                        f"to build confidence, or review the weak topics."
                    ),
                    "suggested_level": prev_level,
                }

        payload = {
            "type": "feedback",
            "state": session["state"],
            "correct": result["correct"],
            "score": result["score"],
            "max_marks": result["max_marks"],
            "pct": result["pct"],
            "explanation": result["explanation"],
            "model_answer": result["model_answer"],
            "missing_keywords": result["missing_keywords"],
            "feedback": result["feedback"],
            "adaptive_hint": adaptive_hint,
            "session_score": session["score"],
            "session_max": session["max_score"],
            "questions_left": session["total"] - session["current_idx"],
        }
        return payload

    def get_adaptive_recommendation(self, session: dict) -> str | None:
        """Return recommendation string based on streaks or accuracy."""
        c_streak = session.get("correct_streak", 0)
        w_streak = session.get("wrong_streak", 0)
        cur_level = session.get("current_level", "easy")
        if c_streak >= ADAPTIVE_STREAK_UP:
            next_level_idx = LEVELS.index(cur_level) + 1 if cur_level in LEVELS else -1
            target_level = LEVELS[next_level_idx] if next_level_idx < len(LEVELS) else "hard"
            return f"Great streak! Try a harder level like {target_level} for more challenge."
        elif w_streak >= ADAPTIVE_STREAK_DOWN:
            prev_level_idx = LEVELS.index(cur_level) - 1 if cur_level in LEVELS else -1
            target_level = LEVELS[prev_level_idx] if prev_level_idx >= 0 else "easy"
            return f"You seem to be struggling. Revise this topic and try easier {target_level} questions."
        return None

    def get_progress(self, session: dict) -> dict:
        """
        Return current progress summary.
        """
        answered = len(session.get("answered", []))
        total = session.get("total", 1)
        score = session.get("score", 0)
        max_score = session.get("max_score", 1) or 1
        pct = round((score / max_score) * 100, 1)
        weak = session.get("weak_topics", [])

        rec = ""
        if weak:
            rec = f"Focus on revising: {', '.join(weak[:3])}."
        elif pct >= 80:
            rec = "Excellent! Try harder questions or mock paper mode."
        elif pct >= 50:
            rec = "Good progress. Practice more medium-level questions."
        else:
            rec = "Review the model answers and retry easy questions first."

        return {
            "type": "progress",
            "answered": answered,
            "total": total,
            "score": score,
            "max_score": max_score,
            "pct": pct,
            "correct_streak": session.get("correct_streak", 0),
            "wrong_streak": session.get("wrong_streak", 0),
            "weak_topics": weak,
            "recommendation": rec,
        }

    def _build_summary(self, session: dict) -> dict:
        """Build end-of-quiz summary payload."""
        score = session.get("score", 0)
        max_score = session.get("max_score", 1) or 1
        pct = round((score / max_score) * 100, 1)
        weak = session.get("weak_topics", [])

        rec = ""
        if weak:
            rec = f"Revise Module topics: {', '.join(weak[:3])}."
        elif pct >= 80:
            rec = "Excellent performance! Try a full mock paper."
        elif pct >= 50:
            rec = "Good attempt. Practice more questions on weak areas."
        else:
            rec = "Review theory and model answers, then retry."

        return {
            "type": "summary",
            "total_score": score,
            "max_score": max_score,
            "pct": pct,
            "weak_topics": weak,
            "recommendation": rec,
            "answered": session.get("answered", []),
        }

    # ----------------------------------------------------------
    # MOCK PAPER
    # ----------------------------------------------------------

    def generate_mock_paper(self, level: str = "mixed", module=None) -> dict:
        """
        Generate a full mock paper with sections A/B/C.

        Section A: 5 × 2-mark (easy)
        Section B: 5 × 5-mark (medium)
        Section C: 3 × 10-mark (hard)

        Returns
        -------
        dict: {"type": "mock_paper", "sections": {"section_a": [...], ...}}
        """
        def _pick(lvl, n, mod=None):
            pool = self.filter_questions(module=mod, level=lvl)
            if len(pool) < n:
                # Pad from full bank at same level
                pool = self.filter_questions(level=lvl)
            random.shuffle(pool)
            return pool[:n]

        if level == "mixed" or level is None:
            sec_a = _pick("easy",   5, module)
            sec_b = _pick("medium", 5, module)
            sec_c = _pick("hard",   3, module)
        else:
            # Single-level paper: use marks distribution anyway
            pool = self.filter_questions(module=module, level=level)
            random.shuffle(pool)
            sec_a = pool[:5]
            sec_b = pool[5:10]
            sec_c = pool[10:13]

        def _fmt(qs, marks_label):
            return [
                {
                    "id": q.get("id"),
                    "marks": marks_label,
                    "topic": q.get("topic", ""),
                    "text": q.get("question", ""),
                    "code": q.get("code"),
                    "type": q.get("type"),
                    "qtype": q.get("type"),
                    "options": q.get("options"),
                    "answer": q.get("answer"),
                    "explanation": q.get("explanation", ""),
                    "exam_tip": q.get("exam_tip", ""),
                }
                for q in qs
            ]

        sec_dict = {
            "section_a": _fmt(sec_a, 2),
            "section_b": _fmt(sec_b, 5),
            "section_c": _fmt(sec_c, 10),
        }
        return {
            "type": "mock_paper",
            "module": module,
            "total_marks": 5*2 + 5*5 + 3*10,
            "sections": sec_dict,
            "section_a": sec_dict["section_a"],
            "section_b": sec_dict["section_b"],
            "section_c": sec_dict["section_c"],
        }

    # ----------------------------------------------------------
    # REVISION
    # ----------------------------------------------------------

    def get_revision(self, module: int) -> list:
        """
        Return important hard questions for a module with model answers.
        """
        qs = self.filter_questions(module=module, level="hard", important_only=True)
        if not qs:
            # Fallback: all hard questions for the module
            qs = self.filter_questions(module=module, level="hard")
        random.shuffle(qs)
        return [
            {
                "id": q.get("id"),
                "topic": q.get("topic", ""),
                "text": q.get("question", ""),
                "code": q.get("code"),
                "marks": q.get("marks", 10),
                "model_answer": q.get("answer", ""),
                "explanation": q.get("explanation", ""),
                "keywords": q.get("keywords", []),
                "exam_tip": q.get("exam_tip", ""),
            }
            for q in qs
        ]

    # ----------------------------------------------------------
    # LEARN NOTES
    # ----------------------------------------------------------

    def get_learn_notes(self, topic: str, level: str) -> str:
        """
        Return exam-oriented notes for a topic from bank answers.

        Finds questions matching topic keywords at the given level,
        assembles their model answers into a revision sheet.
        """
        topic_tokens = set(_tokenize(topic))
        pool = self.filter_questions(level=level)
        matches = []
        for q in pool:
            q_tokens = set(_tokenize(q.get("question", "") + " " + q.get("topic", "")))
            if topic_tokens & q_tokens:
                matches.append(q)

        if not matches:
            # Broaden: ignore level
            for q in self.bank:
                q_tokens = set(_tokenize(q.get("question", "") + " " + q.get("topic", "")))
                if topic_tokens & q_tokens:
                    matches.append(q)

        if not matches:
            return f"No notes found for topic: **{topic}**."

        random.shuffle(matches)
        lines = [f"## Revision Notes: {topic.title()} ({level} level)\n"]
        for q in matches[:6]:
            lines.append(f"**Q: {q['question']}**")
            lines.append(f"A: {q.get('answer', '')}")
            if q.get("exam_tip"):
                lines.append(f"💡 Tip: {q['exam_tip']}")
            lines.append("")
        return "\n".join(lines)

    # ----------------------------------------------------------
    # CODE LAB
    # ----------------------------------------------------------

    def get_code_lab(self, module=None, n: int = 5) -> list:
        """
        Return code_output + debug questions for coding practice.
        """
        pool = self.filter_questions(
            module=module,
            types=["code_output", "debug"],
        )
        if not pool:
            pool = self.filter_questions(types=["code_output", "debug"])
        random.shuffle(pool)
        return [
            {
                "id": q.get("id"),
                "topic": q.get("topic", ""),
                "text": q.get("question", ""),
                "code": q.get("code"),
                "qtype": q.get("type"),
                "marks": q.get("marks"),
                "answer": q.get("answer"),
                "explanation": q.get("explanation", ""),
            }
            for q in pool[:n]
        ]

    # ----------------------------------------------------------
    # DIFFERENCE QUESTION LOOKUP
    # ----------------------------------------------------------

    def find_difference_question(self, keywords: list) -> dict | None:
        """
        Find a 'difference' type question matching given keywords.

        Returns the best matching question dict or None.
        """
        kw_tokens = set(t for k in keywords for t in _tokenize(k))
        best_q = None
        best_overlap = 0
        for q in self.bank:
            if q.get("type") != "difference":
                continue
            q_tokens = set(_tokenize(q.get("question", "") + " " + q.get("topic", "")))
            overlap = len(kw_tokens & q_tokens)
            if overlap > best_overlap:
                best_overlap = overlap
                best_q = q
        return best_q

#!/usr/bin/env python3
"""
validate_bank.py — Validates oops_bank.json schema, coverage, and Java snippets.
Usage: python validate_bank.py [--run-java] [--bank PATH]
"""
import json
import sys
import os
import re
import subprocess
import tempfile
import argparse
from pathlib import Path
from collections import defaultdict

REQUIRED_FIELDS = [
    "id", "module", "topic", "level", "type", "marks",
    "question", "answer", "explanation", "keywords",
    "exam_tip", "source",
]
VALID_LEVELS   = {"easy", "medium", "hard"}
VALID_TYPES    = {"mcq", "true_false", "short", "difference",
                  "code_output", "debug", "program", "long"}
VALID_MODULES  = {1, 2, 3, 4, 5, 6, "bonus"}
VALID_OPT_KEYS = {"A", "B", "C", "D"}


# ─────────────────────────────────────────────────────────────────────
# Schema validation
# ─────────────────────────────────────────────────────────────────────

def validate_schema(q: dict, errors: list) -> None:
    """Validate a single question dict; appends error strings to `errors`."""
    qid = q.get("id", "<no id>")

    # 1. Required fields
    for field in REQUIRED_FIELDS:
        if field not in q or q[field] is None:
            errors.append(f"[{qid}] Missing required field: '{field}'")

    # 2. level
    level = q.get("level")
    if level not in VALID_LEVELS:
        errors.append(f"[{qid}] Invalid level '{level}'; must be one of {VALID_LEVELS}")

    # 3. type
    qtype = q.get("type")
    if qtype not in VALID_TYPES:
        errors.append(f"[{qid}] Invalid type '{qtype}'; must be one of {VALID_TYPES}")

    # 4. module
    module = q.get("module")
    if module not in VALID_MODULES:
        errors.append(
            f"[{qid}] Invalid module '{module}'; must be one of {sorted(str(m) for m in VALID_MODULES)}"
        )

    # 5. marks — must be a positive integer
    marks = q.get("marks")
    if not isinstance(marks, int) or marks <= 0:
        errors.append(f"[{qid}] 'marks' must be a positive integer, got: {marks!r}")

    # 6. MCQ-specific: options + answer
    if qtype == "mcq":
        options = q.get("options")
        if not isinstance(options, dict):
            errors.append(f"[{qid}] MCQ must have an 'options' dict (A/B/C/D)")
        else:
            if set(options.keys()) != VALID_OPT_KEYS:
                errors.append(
                    f"[{qid}] MCQ 'options' must have exactly keys A, B, C, D; got {sorted(options.keys())}"
                )
            answer = q.get("answer")
            if answer not in VALID_OPT_KEYS:
                errors.append(
                    f"[{qid}] MCQ 'answer' must be one of A/B/C/D; got {answer!r}"
                )

    # 7. true_false answer
    if qtype == "true_false":
        answer = q.get("answer")
        if answer not in ("True", "False"):
            errors.append(
                f"[{qid}] true_false 'answer' must be 'True' or 'False'; got {answer!r}"
            )

    # 8. source
    source = q.get("source")
    if source != "syllabus":
        errors.append(f"[{qid}] 'source' must be 'syllabus'; got {source!r}")

    # 9. keywords must be a list
    kw = q.get("keywords")
    if not isinstance(kw, list):
        errors.append(f"[{qid}] 'keywords' must be a list; got {type(kw).__name__}")

    # 10. id format check: M{module_digit}{level_char}{3digits} or BNS{3digits}
    qid_str = q.get("id", "")
    if isinstance(module, int):
        pattern = rf"^M{module}[EMH]\d{{3}}$"
        if not re.match(pattern, qid_str):
            errors.append(
                f"[{qid}] id '{qid_str}' does not match expected format M{module}[EMH]NNN"
            )
    elif module == "bonus":
        if not re.match(r"^BNS\d{3}$", qid_str):
            errors.append(f"[{qid}] Bonus id '{qid_str}' should match BNSxxx")


# ─────────────────────────────────────────────────────────────────────
# Coverage check
# ─────────────────────────────────────────────────────────────────────

def check_coverage(questions: list) -> dict:
    """
    Returns a coverage dict: {module: {level: count}}.
    Prints a table and warns about under-covered module×level cells.
    """
    coverage: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for q in questions:
        module = str(q.get("module", "?"))
        level  = q.get("level", "?")
        coverage[module][level] += 1

    # Order: modules 1–6, then bonus
    module_order = [str(m) for m in range(1, 7)] + ["bonus"]
    level_order  = ["easy", "medium", "hard"]

    # Print table
    print("\nCoverage Table:")
    print(f"{'Module':<8} | {'Easy':>6} | {'Medium':>8} | {'Hard':>6} | {'Total':>7}")
    print("-" * 44)

    warnings = []
    for mod in module_order:
        if mod not in coverage:
            continue
        counts   = coverage[mod]
        easy     = counts.get("easy", 0)
        medium   = counts.get("medium", 0)
        hard     = counts.get("hard", 0)
        total    = easy + medium + hard
        mod_lbl  = mod if mod == "bonus" else mod
        print(f"{mod_lbl:<8} | {easy:>6} | {medium:>8} | {hard:>6} | {total:>7}")
        for lvl, cnt in [("easy", easy), ("medium", medium), ("hard", hard)]:
            if cnt < 10:
                warnings.append(
                    f"  WARNING: Module {mod} / {lvl} has only {cnt} question(s) (< 10 required)"
                )

    print()
    if warnings:
        for w in warnings:
            print(w)
    else:
        print("Coverage OK — every module×level has ≥ 10 questions.")

    return dict(coverage)


# ─────────────────────────────────────────────────────────────────────
# Java snippet runner
# ─────────────────────────────────────────────────────────────────────

def _find_public_class(code: str) -> str | None:
    """Return the class with main() or public class name from Java source."""
    m = re.search(r'\bpublic\s+class\s+(\w+)', code)
    if m:
        return m.group(1)
    
    # Priority: find class that encloses public static void main (exclude comments)
    clean_code = re.sub(r'//.*', '', code)
    classes = list(re.finditer(r'\bclass\s+(\w+)', clean_code))
    main_match = re.search(r'\bpublic\s+static\s+void\s+main\b', clean_code)
    if main_match and classes:
        main_pos = main_match.start()
        enclosing = [cm.group(1) for cm in classes if cm.start() < main_pos]
        if enclosing:
            return enclosing[-1]

    # Fallback: any class
    m = re.search(r'\bclass\s+(\w+)', clean_code)
    return m.group(1) if m else None


def _normalize(text: str) -> str:
    """Normalize whitespace for comparison."""
    return re.sub(r'\s+', ' ', text.strip())


def run_java_snippet(code: str, expected_output: str) -> tuple[bool, str]:
    """
    Compile and run a Java code snippet.
    Returns (passed, actual_output).
    """
    class_name = _find_public_class(code)
    if class_name is None:
        return False, "ERROR: could not detect class name in snippet"

    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, f"{class_name}.java")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Compile
        try:
            result = subprocess.run(
                ["javac", src_path],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except FileNotFoundError:
            return False, "ERROR: javac not found — please install a JDK and add it to PATH"
        except subprocess.TimeoutExpired:
            return False, "ERROR: javac timed out"

        if result.returncode != 0:
            return False, f"COMPILE ERROR:\n{result.stderr.strip()}"

        # Run
        try:
            run_result = subprocess.run(
                ["java", "-cp", tmpdir, class_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            return False, "ERROR: java not found — please install a JDK and add it to PATH"
        except subprocess.TimeoutExpired:
            return False, "ERROR: java run timed out"

        actual = run_result.stdout
        if run_result.returncode != 0:
            actual += run_result.stderr

        passed = _normalize(actual) == _normalize(expected_output)
        return passed, actual.strip()


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate oops_bank.json schema, coverage, and Java snippets."
    )
    parser.add_argument(
        "--run-java", action="store_true",
        help="Compile and run Java code_output snippets to verify correctness",
    )
    parser.add_argument(
        "--bank", default="oops_bank.json",
        help="Path to the question bank JSON file (default: oops_bank.json)",
    )
    args = parser.parse_args()

    bank_path = Path(args.bank)
    if not bank_path.exists():
        print(f"ERROR: '{bank_path}' not found")
        sys.exit(1)

    with open(bank_path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"ERROR: Invalid JSON in '{bank_path}': {exc}")
            sys.exit(1)

    questions = data.get("questions", [])
    print(f"Total questions loaded: {len(questions)}")

    has_errors = False

    # ── 1. Schema validation ──────────────────────────────────────────
    print("\n--- Schema Validation ---")
    schema_errors: list[str] = []
    for q in questions:
        validate_schema(q, schema_errors)

    if schema_errors:
        has_errors = True
        print(f"Found {len(schema_errors)} schema error(s):")
        for err in schema_errors:
            print(f"  {err}")
    else:
        print("No schema errors found.")

    # ── 2. ID uniqueness ──────────────────────────────────────────────
    print("\n--- ID Uniqueness Check ---")
    seen_ids: dict[str, int] = {}
    duplicates: list[str] = []
    for idx, q in enumerate(questions):
        qid = q.get("id", f"<missing id at index {idx}>")
        if qid in seen_ids:
            duplicates.append(
                f"Duplicate id '{qid}' at index {idx} (first seen at index {seen_ids[qid]})"
            )
        else:
            seen_ids[qid] = idx

    if duplicates:
        has_errors = True
        print(f"Found {len(duplicates)} duplicate id(s):")
        for d in duplicates:
            print(f"  {d}")
    else:
        print(f"All {len(seen_ids)} ids are unique.")

    # ── 3. Coverage ───────────────────────────────────────────────────
    print("\n--- Coverage Check ---")
    check_coverage(questions)

    # ── 4. Java snippet validation ────────────────────────────────────
    if args.run_java:
        print("\n--- Java Snippet Validation ---")
        java_qs = [q for q in questions if q.get("type") == "code_output" and q.get("code")]
        print(f"Running {len(java_qs)} code_output snippet(s)…")
        passed_count = 0
        failed_count = 0
        for q in java_qs:
            qid     = q.get("id", "?")
            code    = q["code"]
            expected = q.get("answer", "")
            ok, actual = run_java_snippet(code, expected)
            status = "PASS" if ok else "FAIL"
            if ok:
                passed_count += 1
                print(f"  [{status}] {qid}")
            else:
                failed_count += 1
                has_errors = True
                print(f"  [{status}] {qid}")
                print(f"    Expected : {_normalize(expected)!r}")
                print(f"    Got      : {_normalize(actual)!r}")

        print(f"\nJava results: {passed_count} passed, {failed_count} failed out of {len(java_qs)}")

    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 44)
    if has_errors:
        print("RESULT: Validation FAILED — fix errors above.")
        sys.exit(1)
    else:
        print("RESULT: All checks PASSED ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()

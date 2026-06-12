#!/usr/bin/env python3
"""Standalone qhsJSON v4 validator for CoachPrash content files.

No Flask or database dependencies required.

Usage:
    python content/validate_qhsjson.py                     # validate all content/*.json
    python content/validate_qhsjson.py content/foo.json     # validate specific file(s)
    python content/validate_qhsjson.py --no-warnings        # errors only
    python content/validate_qhsjson.py --verbose            # show per-concept stats
    python content/validate_qhsjson.py --strict             # AI artifacts become errors

Exit codes:
    0 = no errors (warnings are OK)
    1 = errors found (or AI artifacts with --strict)
    2 = script failure (no files, bad args, etc.)
"""

import json
import re
import sys
import os
import glob
import argparse
from pathlib import Path

# --- Try to import jsonschema; degrade gracefully ---
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# ──────────────────────────────────────────────────────────────
# Color helpers (ANSI codes, auto-disabled when not a terminal)
# ──────────────────────────────────────────────────────────────

def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

USE_COLOR = _supports_color()

def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

def red(t):    return _c("31", t)
def green(t):  return _c("32", t)
def yellow(t): return _c("33", t)
def bold(t):   return _c("1", t)
def dim(t):    return _c("2", t)


# ──────────────────────────────────────────────────────────────
# AI artifact patterns (Pass 3)
# ──────────────────────────────────────────────────────────────

AI_ARTIFACT_PATTERNS = [
    # Thinking phrases
    ("thinking", re.compile(r"\bwait,", re.I), "Thinking phrase: 'wait,'"),
    ("thinking", re.compile(r"\bactually,", re.I), "Thinking phrase: 'actually,'"),
    ("thinking", re.compile(r"\bhmm\b", re.I), "Thinking phrase: 'hmm'"),
    ("thinking", re.compile(r"\blet me reconsider\b", re.I), "Thinking: 'let me reconsider'"),
    ("thinking", re.compile(r"\blet me recalculate\b", re.I), "Thinking: 'let me recalculate'"),
    ("thinking", re.compile(r"\bI think\b", re.I), "Thinking phrase: 'I think'"),
    ("thinking", re.compile(r"\bI believe\b", re.I), "Thinking phrase: 'I believe'"),
    ("thinking", re.compile(r"\bupon reflection\b", re.I), "Thinking: 'upon reflection'"),
    ("thinking", re.compile(r"\bon second thought\b", re.I), "Thinking: 'on second thought'"),
    ("thinking", re.compile(r"\blooking at this again\b", re.I), "Thinking: 'looking at this again'"),
    # Self-correction
    ("self-correction", re.compile(r"\bthe correct answer should be\b", re.I), "Self-correction remnant"),
    ("self-correction", re.compile(r"\bthe answer is actually\b", re.I), "Self-correction remnant"),
    ("self-correction", re.compile(r"\bI made an error\b", re.I), "Self-correction remnant"),
    ("self-correction", re.compile(r"\bI made a mistake\b", re.I), "Self-correction remnant"),
    ("self-correction", re.compile(r"\bcorrection:", re.I), "Self-correction remnant"),
    ("self-correction", re.compile(r"\bcorrected:", re.I), "Self-correction remnant"),
    # Hedging
    ("hedging", re.compile(r"\bclosest to\b", re.I), "Hedging: 'closest to'"),
    ("hedging", re.compile(r"\bclosest answer\b", re.I), "Hedging: 'closest answer'"),
    ("hedging", re.compile(r"\bbest approximation\b", re.I), "Hedging: 'best approximation'"),
    ("hedging", re.compile(r"\bapproximately matches\b", re.I), "Hedging: 'approximately matches'"),
    ("hedging", re.compile(r"\bnone of the above exactly\b", re.I), "Hedging: 'none of the above exactly'"),
    # AI persona leaks
    ("persona", re.compile(r"\bas an AI\b", re.I), "AI persona leak"),
    ("persona", re.compile(r"\bas a language model\b", re.I), "AI persona leak"),
    ("persona", re.compile(r"\bI cannot\b", re.I), "AI persona leak: 'I cannot'"),
    ("persona", re.compile(r"\bI'm sorry\b", re.I), "AI persona leak: 'I'm sorry'"),
]


# ──────────────────────────────────────────────────────────────
# Schema validation (Pass 1)
# ──────────────────────────────────────────────────────────────

def load_schema():
    """Load the qhsJSON schema from the same directory as this script."""
    schema_path = Path(__file__).parent / "qhsjson_schema.json"
    if not schema_path.exists():
        return None
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data, schema):
    """Run JSON Schema validation. Returns list of error strings."""
    if not HAS_JSONSCHEMA or schema is None:
        return None  # None means skipped, [] means passed

    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = " > ".join(str(p) for p in error.absolute_path) or "root"
        # Simplify oneOf errors (hints/steps) to avoid confusing output
        if error.validator == "oneOf":
            msg = f"  {red('ERROR')} [schema] {path}: must be a string or valid object"
        else:
            msg = f"  {red('ERROR')} [schema] {path}: {error.message}"
        errors.append(msg)
    return errors


# ──────────────────────────────────────────────────────────────
# Semantic validation (Pass 2)
# ──────────────────────────────────────────────────────────────

def validate_semantics(data, filename):
    """Check rules JSON Schema cannot express.

    Returns (errors: list[str], warnings: list[str], stats: dict).
    """
    errors = []
    warnings = []
    stats = {
        "topics": 0,
        "concepts": 0,
        "problem_sets": 0,
        "problems": 0,
        "mcq": 0,
        "ftb": 0,
        "frq": 0,
        "hints": 0,
        "solutions": 0,
    }

    concept_slugs = {}  # slug -> location string (for duplicate detection)

    topics = data.get("topics", [])
    if not isinstance(topics, list) or len(topics) == 0:
        errors.append(f"  {red('ERROR')} Root: 'topics' array is missing or empty")
        return errors, warnings, stats

    for ti, topic in enumerate(topics):
        tname = topic.get("name", topic.get("title", f"Topic {ti+1}"))
        tloc = f"Topic {ti+1} ({tname})"
        stats["topics"] += 1

        # ERROR: topic uses 'title' instead of 'name'
        if "title" in topic and "name" not in topic:
            errors.append(
                f"  {red('ERROR')} {tloc}: uses 'title' instead of 'name' at topic level"
            )

        # WARN: missing description
        if not topic.get("description"):
            warnings.append(f"  {yellow('WARN')}  {tloc}: missing 'description'")

        concepts = topic.get("concepts", [])
        if not isinstance(concepts, list) or len(concepts) == 0:
            errors.append(f"  {red('ERROR')} {tloc}: 'concepts' array is missing or empty")
            continue

        for ci, concept in enumerate(concepts):
            ctitle = concept.get("title", f"Concept {ci+1}")
            cloc = f"{tloc} > Concept {ci+1} ({ctitle})"
            stats["concepts"] += 1

            # Check for duplicate slugs
            cslug = concept.get("slug")
            if cslug:
                if cslug in concept_slugs:
                    errors.append(
                        f"  {red('ERROR')} {cloc}: duplicate slug '{cslug}' "
                        f"(first used at {concept_slugs[cslug]})"
                    )
                else:
                    concept_slugs[cslug] = cloc
            else:
                warnings.append(f"  {yellow('WARN')}  {cloc}: missing explicit 'slug' (will be auto-generated)")

            # WARN: missing content_html
            if not concept.get("content_html"):
                warnings.append(f"  {yellow('WARN')}  {cloc}: missing 'content_html'")

            problem_sets = concept.get("problem_sets", [])
            if not isinstance(problem_sets, list) or len(problem_sets) == 0:
                errors.append(f"  {red('ERROR')} {cloc}: 'problem_sets' array is missing or empty")
                continue

            for psi, ps in enumerate(problem_sets):
                pstitle = ps.get("title", ps.get("name", f"PS {psi+1}"))
                psloc = f"{cloc} > PS {psi+1} ({pstitle})"
                stats["problem_sets"] += 1

                # ERROR: problem_set uses 'name' instead of 'title'
                if "name" in ps and "title" not in ps:
                    errors.append(
                        f"  {red('ERROR')} {psloc}: uses 'name' instead of 'title' "
                        f"at problem_set level"
                    )

                problems = ps.get("problems", [])
                if not isinstance(problems, list) or len(problems) == 0:
                    errors.append(f"  {red('ERROR')} {psloc}: 'problems' array is missing or empty")
                    continue

                for pi, prob in enumerate(problems):
                    ploc = f"{psloc} > Problem {pi+1}"
                    stats["problems"] += 1
                    ptype = prob.get("problem_type", "mcq")

                    # Count by type
                    if ptype == "mcq":
                        stats["mcq"] += 1
                    elif ptype == "ftb":
                        stats["ftb"] += 1
                    elif ptype == "frq":
                        stats["frq"] += 1
                    else:
                        errors.append(
                            f"  {red('ERROR')} {ploc}: invalid problem_type '{ptype}' "
                            f"(must be mcq, ftb, or frq)"
                        )

                    # ERROR: deprecated answer_options
                    if "answer_options" in prob:
                        errors.append(
                            f"  {red('ERROR')} {ploc}: uses deprecated 'answer_options' "
                            f"(rename to 'choices' with 'text' instead of 'value')"
                        )

                    # --- MCQ checks ---
                    if ptype == "mcq":
                        choices = prob.get("choices", [])
                        if not choices:
                            errors.append(f"  {red('ERROR')} {ploc}: MCQ missing 'choices' array")
                        else:
                            correct = [c for c in choices if c.get("is_correct")]
                            if len(correct) == 0:
                                errors.append(f"  {red('ERROR')} {ploc}: MCQ has no correct choice (need exactly 1)")
                            elif len(correct) > 1:
                                errors.append(f"  {red('ERROR')} {ploc}: MCQ has {len(correct)} correct choices (need exactly 1)")
                            if len(choices) == 1:
                                warnings.append(f"  {yellow('WARN')}  {ploc}: MCQ has only 1 choice")
                            elif len(choices) < 4 and len(choices) > 1:
                                warnings.append(f"  {yellow('WARN')}  {ploc}: MCQ has {len(choices)} choices (typically 4; OK for True/False)")

                            # Check choice text
                            for chi, ch in enumerate(choices):
                                if not ch.get("text") and not ch.get("choice_text"):
                                    errors.append(f"  {red('ERROR')} {ploc}: Choice {chi+1} has no 'text'")

                    # --- FTB checks ---
                    if ptype == "ftb":
                        ca = prob.get("correct_answer", "")
                        if not ca or not str(ca).strip():
                            errors.append(f"  {red('ERROR')} {ploc}: FTB missing 'correct_answer'")

                    # --- FRQ checks ---
                    if ptype == "frq":
                        if not prob.get("correct_answer") and not prob.get("sample_answer"):
                            warnings.append(f"  {yellow('WARN')}  {ploc}: FRQ missing 'correct_answer' (model answer for self-grading)")
                        if "sample_answer" in prob and "correct_answer" not in prob:
                            warnings.append(
                                f"  {yellow('WARN')}  {ploc}: has 'sample_answer' but no 'correct_answer' "
                                f"(loader only reads 'correct_answer')"
                            )
                        if not prob.get("rubric"):
                            warnings.append(f"  {yellow('WARN')}  {ploc}: FRQ missing 'rubric'")

                    # --- Hint checks ---
                    hints = prob.get("hints", [])
                    if hints:
                        stats["hints"] += len(hints)
                        for hi, h in enumerate(hints):
                            if isinstance(h, dict):
                                if h.get("hint_text") and not h.get("text"):
                                    warnings.append(
                                        f"  {yellow('WARN')}  {ploc} > Hint {hi+1}: uses 'hint_text' "
                                        f"instead of 'text' (both work, but 'text' is canonical)"
                                    )
                                if "hint_cost" in h and "cost_points" not in h:
                                    warnings.append(
                                        f"  {yellow('WARN')}  {ploc} > Hint {hi+1}: uses 'hint_cost' "
                                        f"instead of 'cost_points' (loader reads 'cost_points')"
                                    )
                    else:
                        warnings.append(f"  {yellow('WARN')}  {ploc}: no hints")

                    # --- Solution step checks ---
                    steps = prob.get("solution_steps", prob.get("solution", []))
                    if steps:
                        stats["solutions"] += len(steps) if isinstance(steps, list) else 0
                        if isinstance(steps, list):
                            for si, s in enumerate(steps):
                                if isinstance(s, dict):
                                    if "step" in s and "step_number" not in s:
                                        warnings.append(
                                            f"  {yellow('WARN')}  {ploc} > Step {si+1}: uses 'step' "
                                            f"instead of 'step_number'"
                                        )
                    else:
                        warnings.append(f"  {yellow('WARN')}  {ploc}: no solution_steps")

    return errors, warnings, stats


# ──────────────────────────────────────────────────────────────
# AI artifact detection (Pass 3)
# ──────────────────────────────────────────────────────────────

def _extract_text_fields(problem):
    """Yield (field_name, text) tuples for all scannable text in a problem."""
    # Question
    q = problem.get("question_html", "")
    if q:
        yield ("question_html", str(q))

    # Correct answer
    ca = problem.get("correct_answer", "")
    if ca:
        yield ("correct_answer", str(ca))

    # MCQ choices
    for ci, ch in enumerate(problem.get("choices", [])):
        text = ch.get("text") or ch.get("choice_text", "") if isinstance(ch, dict) else ""
        if text:
            yield (f"Choice {ci+1}", str(text))

    # Hints
    for hi, h in enumerate(problem.get("hints", [])):
        if isinstance(h, str):
            text = h
        elif isinstance(h, dict):
            text = h.get("text") or h.get("hint_text", "")
        else:
            text = ""
        if text:
            yield (f"Hint {hi+1}", str(text))

    # Solution steps
    steps = problem.get("solution_steps", problem.get("solution", []))
    if isinstance(steps, list):
        for si, s in enumerate(steps):
            if isinstance(s, str):
                text = s
            elif isinstance(s, dict):
                text = s.get("text") or s.get("text_html", "")
            else:
                text = ""
            if text:
                yield (f"Step {si+1}", str(text))


def _check_latex_balance(text):
    """Return list of issues with unmatched LaTeX delimiters."""
    issues = []
    # Inline math: \( ... \)
    opens = len(re.findall(r"\\\(", text))
    closes = len(re.findall(r"\\\)", text))
    if opens != closes:
        issues.append(f"Unmatched inline LaTeX: {opens} \\( vs {closes} \\)")
    # Display math: \[ ... \]
    opens = len(re.findall(r"\\\[", text))
    closes = len(re.findall(r"\\\]", text))
    if opens != closes:
        issues.append(f"Unmatched display LaTeX: {opens} \\[ vs {closes} \\]")
    return issues


def validate_ai_artifacts(data):
    """Pass 3: Detect AI-generated content artifacts.

    Returns (issues: list[str], count: int).
    """
    issues = []
    count = 0

    topics = data.get("topics", [])
    if not isinstance(topics, list):
        return issues, count

    for ti, topic in enumerate(topics):
        tname = topic.get("name", topic.get("title", f"Topic {ti+1}"))
        tloc = f"Topic {ti+1} ({tname})"

        for ci, concept in enumerate(topic.get("concepts", [])):
            ctitle = concept.get("title", f"Concept {ci+1}")
            cloc = f"{tloc} > Concept {ci+1} ({ctitle})"

            for psi, ps in enumerate(concept.get("problem_sets", [])):
                pstitle = ps.get("title", ps.get("name", f"PS {psi+1}"))
                psloc = f"{cloc} > PS {psi+1} ({pstitle})"

                for pi, prob in enumerate(ps.get("problems", [])):
                    ploc = f"{psloc} > Problem {pi+1}"

                    for field_name, text in _extract_text_fields(prob):
                        # Pattern matching
                        for _cat, pattern, desc in AI_ARTIFACT_PATTERNS:
                            match = pattern.search(text)
                            if match:
                                snippet = match.group()
                                issues.append(
                                    f"  {{LEVEL}}  [ai-artifact] {ploc} > "
                                    f"{field_name}: {desc} (matched: '{snippet}')"
                                )
                                count += 1

                        # LaTeX balance
                        for latex_issue in _check_latex_balance(text):
                            issues.append(
                                f"  {{LEVEL}}  [ai-artifact] {ploc} > "
                                f"{field_name}: {latex_issue}"
                            )
                            count += 1

    return issues, count


# ──────────────────────────────────────────────────────────────
# File validation (combines all passes)
# ──────────────────────────────────────────────────────────────

def validate_file(filepath, schema, show_warnings=True, verbose=False, strict=False):
    """Validate a single qhsJSON file. Returns (error_count, warning_count)."""
    filename = os.path.basename(filepath)
    print(f"\n{bold('===')} {bold(filename)} {bold('===')}")

    # Parse JSON
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  {red('ERROR')} Invalid JSON: {e}")
        return 1, 0
    except Exception as e:
        print(f"  {red('ERROR')} Cannot read file: {e}")
        return 1, 0

    error_count = 0
    warning_count = 0

    # Pass 1: Schema validation
    schema_errors = validate_schema(data, schema)
    if schema_errors is None:
        print(f"  {dim('SKIP')}  Schema validation (jsonschema not installed)")
    elif len(schema_errors) == 0:
        print(f"  {green('PASS')}  Schema validation")
    else:
        error_count += len(schema_errors)
        print(f"  {red('FAIL')}  Schema validation ({len(schema_errors)} errors)")
        for e in schema_errors[:20]:  # Cap to avoid flooding
            print(e)
        if len(schema_errors) > 20:
            print(f"  {dim('...')}  ({len(schema_errors) - 20} more schema errors)")

    # Pass 2: Semantic validation
    sem_errors, sem_warnings, stats = validate_semantics(data, filename)
    error_count += len(sem_errors)
    warning_count += len(sem_warnings)

    if sem_errors:
        for e in sem_errors:
            print(e)

    if show_warnings and sem_warnings:
        for w in sem_warnings:
            print(w)

    # Pass 3: AI artifact detection
    ai_issues, ai_count = validate_ai_artifacts(data)
    if ai_count == 0:
        print(f"  {green('PASS')}  AI artifact scan")
    else:
        if strict:
            error_count += ai_count
            label = red('FAIL')
            level_str = red('ERROR')
        else:
            warning_count += ai_count
            label = yellow('WARN')
            level_str = yellow('WARN')
        print(f"  {label}  AI artifact scan ({ai_count} issues)")
        if show_warnings or strict:
            for issue in ai_issues:
                print(issue.replace("{LEVEL}", level_str))

    # Stats line
    if stats["topics"] > 0:
        type_breakdown = f"{stats['mcq']} MCQ, {stats['ftb']} FTB, {stats['frq']} FRQ"
        print(
            f"  {dim('Stats')} {stats['topics']} topics, {stats['concepts']} concepts, "
            f"{stats['problem_sets']} problem sets, {stats['problems']} problems ({type_breakdown})"
        )
        if verbose:
            print(
                f"         {stats['hints']} hints, {stats['solutions']} solution steps"
            )
            if ai_count > 0:
                print(f"         {ai_count} AI artifact warnings")

    # Result line
    if error_count == 0 and warning_count == 0:
        print(f"  {green('Result: PASS')} - no errors, no warnings")
    elif error_count == 0:
        print(f"  {green('Result: PASS')} - 0 errors, {warning_count} warnings")
    else:
        print(f"  {red('Result: FAIL')} - {error_count} errors, {warning_count} warnings")

    return error_count, warning_count


# ──────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Validate qhsJSON v4 content files for CoachPrash."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific JSON files to validate. Defaults to all content/*.json files.",
    )
    parser.add_argument(
        "--no-warnings",
        action="store_true",
        help="Suppress warnings (show errors only).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed stats per file.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote AI artifact warnings to errors (useful for CI/pre-commit).",
    )
    args = parser.parse_args()

    # Discover files
    if args.files:
        files = args.files
    else:
        # Auto-discover from content/ directory
        content_dir = Path(__file__).parent
        files = sorted(content_dir.glob("*.json"))
        # Exclude the schema file itself
        files = [str(f) for f in files if f.name != "qhsjson_schema.json"]

    if not files:
        print(f"{red('ERROR')}: No JSON files found to validate.")
        sys.exit(2)

    # Load schema
    schema = load_schema()
    if not HAS_JSONSCHEMA:
        print(f"{yellow('Note')}: 'jsonschema' package not installed. Schema validation will be skipped.")
        print(f"       Install with: pip install jsonschema>=4.0")
    elif schema is None:
        print(f"{yellow('Note')}: qhsjson_schema.json not found. Schema validation will be skipped.")

    # Validate each file
    total_errors = 0
    total_warnings = 0
    files_with_errors = 0
    files_with_warnings = 0

    for filepath in files:
        if not os.path.exists(filepath):
            print(f"\n{red('ERROR')}: File not found: {filepath}")
            total_errors += 1
            files_with_errors += 1
            continue

        errs, warns = validate_file(
            filepath,
            schema,
            show_warnings=not args.no_warnings,
            verbose=args.verbose,
            strict=args.strict,
        )
        total_errors += errs
        total_warnings += warns
        if errs > 0:
            files_with_errors += 1
        if warns > 0:
            files_with_warnings += 1

    # Cross-file slug collision check (only when validating multiple files)
    if len(files) > 1:
        slug_sources = {}
        collision_count = 0
        for filepath in files:
            if not os.path.exists(filepath):
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    fdata = json.load(f)
                course = fdata.get('course_slug', os.path.basename(filepath))
                for t in fdata.get('topics', []):
                    for c in t.get('concepts', []):
                        s = c.get('slug', '')
                        if s in slug_sources and slug_sources[s] != course:
                            print(f"  {red('ERROR')} Slug collision: '{s}' in both '{slug_sources[s]}' and '{course}'")
                            collision_count += 1
                        else:
                            slug_sources[s] = course
            except (json.JSONDecodeError, OSError):
                pass
        if collision_count > 0:
            total_errors += collision_count
            files_with_errors += 1  # At least one file is affected
        else:
            print(f"\n  {green('PASS')}  Cross-file slug collision check ({len(slug_sources)} unique slugs)")

    # Summary
    print(f"\n{bold('============ Summary ============')}")
    print(f"  Files:    {len(files)} checked | {files_with_errors} with errors | {files_with_warnings} with warnings")
    print(f"  Total:    {total_errors} errors, {total_warnings} warnings")

    if total_errors == 0:
        print(f"  {green('All files passed validation.')}")
    else:
        print(f"  {red(f'{files_with_errors} file(s) have errors that must be fixed.')}")

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()

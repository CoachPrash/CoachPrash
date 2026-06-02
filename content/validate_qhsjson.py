#!/usr/bin/env python3
"""Standalone qhsJSON v4 validator for CoachPrash content files.

No Flask or database dependencies required.

Usage:
    python content/validate_qhsjson.py                     # validate all content/*.json
    python content/validate_qhsjson.py content/foo.json     # validate specific file(s)
    python content/validate_qhsjson.py --no-warnings        # errors only
    python content/validate_qhsjson.py --verbose            # show per-concept stats

Exit codes:
    0 = no errors (warnings are OK)
    1 = errors found
    2 = script failure (no files, bad args, etc.)
"""

import json
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
# File validation (combines both passes)
# ──────────────────────────────────────────────────────────────

def validate_file(filepath, schema, show_warnings=True, verbose=False):
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
        )
        total_errors += errs
        total_warnings += warns
        if errs > 0:
            files_with_errors += 1
        if warns > 0:
            files_with_warnings += 1

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

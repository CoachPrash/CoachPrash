"""Math expression standardizer for FTB answer checking.

Provides SymPy-based symbolic equivalence checking as a fallback when
literal string matching fails. Handles whitespace, Unicode, implicit
multiplication, trig identities, and constant-of-integration differences.
"""
import re
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Unicode → ASCII normalization map
_UNICODE_MAP = {
    'π': 'pi',
    '∞': 'oo',
    '²': '**2',
    '³': '**3',
    '⁴': '**4',
    '÷': '/',
    '·': '*',
    '×': '*',
    '−': '-',      # Unicode minus → ASCII hyphen
    '\u2212': '-',  # another minus variant
}

# Words that signal descriptive (non-math) text
_TEXT_STARTERS = {
    'yes', 'no', 'true', 'false', 'the', 'it', 'they', 'a', 'an',
    'this', 'that', 'there', 'neither', 'both', 'either',
    'local', 'global', 'removable', 'jump', 'infinite',
    'horizontal', 'vertical', 'hole', 'continuous', 'discontinuous',
    'increasing', 'decreasing', 'concave', 'inconclusive',
    'dollars', 'liters', 'meters', 'seconds', 'miles',
}

# Math-indicative tokens
_MATH_TOKENS = re.compile(
    r'(?:'
    r'\^|sqrt|sin|cos|tan|sec|csc|cot|ln|log|exp|arcsin|arccos|arctan|'
    r'arcsec|arccsc|arccot|pi|infinity|inf|Abs|'
    r'\d+/\d+'  # fraction pattern like 3/7
    r')',
    re.IGNORECASE,
)

# Pattern for 3+ consecutive English words (signals descriptive text)
_MULTI_WORD = re.compile(r'[a-zA-Z]{2,}\s+[a-zA-Z]{2,}\s+[a-zA-Z]{2,}')


def check_math_equivalent(submitted: str, correct_answer: str):
    """Check if submitted answer is mathematically equivalent to correct_answer.

    The correct_answer may contain || separators for alternate forms.

    Returns:
        True  — symbolically equivalent to at least one variant
        None  — could not determine (caller should use string-match result)
    """
    if not submitted or not correct_answer:
        return None

    variants = [v.strip() for v in correct_answer.split('||')]

    for variant in variants:
        if not variant:
            continue
        if not _is_math_expression(variant):
            continue

        result = _compare_single(submitted.strip(), variant)
        if result is True:
            return True

    return None


def _compare_single(submitted, correct):
    """Compare a single submitted answer against a single correct variant."""
    # Detect +C (constant of integration)
    allow_constant = False
    sub_clean = submitted
    cor_clean = correct

    c_pattern = re.compile(r'\s*\+\s*C\s*$', re.IGNORECASE)
    if c_pattern.search(correct):
        allow_constant = True
        cor_clean = c_pattern.sub('', correct)
        sub_clean = c_pattern.sub('', submitted)

    sub_expr = _parse_expr_safe(_preprocess(sub_clean))
    cor_expr = _parse_expr_safe(_preprocess(cor_clean))

    if sub_expr is None or cor_expr is None:
        return None

    return _exprs_equivalent(sub_expr, cor_expr, allow_constant)


def _is_math_expression(text):
    """Heuristic: does this look like a math expression vs descriptive text?"""
    # Normalize Unicode before checking
    stripped = text.strip()
    for old, new in _UNICODE_MAP.items():
        stripped = stripped.replace(old, new)
    stripped = stripped.lower()

    # Short numeric answers are math
    try:
        float(stripped)
        return True
    except ValueError:
        pass

    # Starts with a common English word → not math
    first_word = stripped.split()[0] if stripped.split() else ''
    if first_word in _TEXT_STARTERS:
        return False

    # 3+ consecutive English words → descriptive text
    if _MULTI_WORD.search(stripped):
        return False

    # Contains math-indicative tokens → math
    if _MATH_TOKENS.search(stripped):
        return True

    # Contains operator between alphanumeric chars (like x+1, 2x-3)
    if re.search(r'[a-zA-Z0-9]\s*[+\-*/^]\s*[a-zA-Z0-9]', stripped):
        return True

    # Single variable or simple identifier — not worth SymPy
    if re.match(r'^[a-zA-Z]$', stripped):
        return False

    return False


def _preprocess(text):
    """Normalize a math string before SymPy parsing."""
    s = text.strip()

    # Unicode normalization
    for old, new in _UNICODE_MAP.items():
        s = s.replace(old, new)

    # Absolute value: |expr| → Abs(expr)
    # Match paired pipes, being careful not to match || (already split)
    s = re.sub(r'\|([^|]+)\|', r'Abs(\1)', s)

    # e^ → exp() conversion — handle e^(...) and e^simple
    s = re.sub(r'\be\^(\([^)]+\))', r'exp\1', s)
    s = re.sub(r'\be\^(\w+)', r'exp(\1)', s)

    # ln → log (SymPy uses log for natural log)
    s = re.sub(r'\bln\b', 'log', s)

    # Caret → power
    s = s.replace('^', '**')

    # Handle trig squared notation: sin**2(x) → sin(x)**2, cos**2 x → cos(x)**2
    s = re.sub(
        r'(sin|cos|tan|sec|csc|cot)\*\*(\d+)\s*\(([^)]+)\)',
        r'\1(\3)**\2', s
    )
    s = re.sub(
        r'(sin|cos|tan|sec|csc|cot)\*\*(\d+)\s+(\w+)',
        r'\1(\3)**\2', s
    )

    # sec/csc/cot → 1/cos, 1/sin, cos/sin
    s = re.sub(r'\bsec\(([^)]+)\)', r'(1/cos(\1))', s)
    s = re.sub(r'\bcsc\(([^)]+)\)', r'(1/sin(\1))', s)
    s = re.sub(r'\bcot\(([^)]+)\)', r'(cos(\1)/sin(\1))', s)

    # Handle sec/csc/cot without parens: sec x → 1/cos(x)
    s = re.sub(r'\bsec\s+(\w+)', r'(1/cos(\1))', s)
    s = re.sub(r'\bcsc\s+(\w+)', r'(1/sin(\1))', s)
    s = re.sub(r'\bcot\s+(\w+)', r'(cos(\1)/sin(\1))', s)

    # Handle trig without parens: sin x → sin(x), cos 2x → cos(2*x)
    s = re.sub(r'\b(sin|cos|tan)\s+(\w+)', r'\1(\2)', s)

    # Handle = sign: "y = 5x - 1" → just the RHS if it has =
    if '=' in s and not s.startswith('='):
        parts = s.split('=', 1)
        # If LHS is a single variable, compare just the RHS
        if re.match(r'^\s*[a-zA-Z]\s*$', parts[0]):
            s = parts[1].strip()

    return s


@lru_cache(maxsize=512)
def _parse_expr_safe(text):
    """Parse a preprocessed math string into a SymPy expression.

    Returns None if parsing fails.
    """
    try:
        from sympy import Symbol, E, pi, oo, Abs, log, exp, sqrt
        from sympy import sin, cos, tan
        from sympy import Rational  # noqa: F401
        from sympy.parsing.sympy_parser import (
            parse_expr,
            standard_transformations,
            implicit_multiplication_application,
            convert_xor,
        )

        local_dict = {
            'e': E, 'E': E,
            'pi': pi, 'Pi': pi,
            'oo': oo,
            'Abs': Abs, 'abs': Abs,
            'log': log, 'ln': log,
            'exp': exp,
            'sqrt': sqrt,
            'sin': sin, 'cos': cos, 'tan': tan,
            'x': Symbol('x'),
            'y': Symbol('y'),
            'n': Symbol('n'),
            't': Symbol('t'),
            'k': Symbol('k'),
            'r': Symbol('r'),
            's': Symbol('s'),
            'u': Symbol('u'),
            'v': Symbol('v'),
            'w': Symbol('w'),
            'a': Symbol('a'),
            'b': Symbol('b'),
            'C': Symbol('C'),
            'A': Symbol('A'),
        }

        transformations = (
            standard_transformations
            + (implicit_multiplication_application, convert_xor)
        )

        expr = parse_expr(text, local_dict=local_dict,
                          transformations=transformations, evaluate=True)
        return expr

    except Exception:
        return None


def _exprs_equivalent(a, b, allow_constant_diff=False):
    """Check if two SymPy expressions are equivalent.

    Three-tier approach:
    1. simplify(a - b) == 0
    2. trigsimp(a - b) == 0
    3. Numerical evaluation at random points
    """
    try:
        from sympy import simplify, trigsimp, Rational
        import signal
        import threading

        diff = a - b

        # Tier 1: direct simplification
        result = [None]

        def _simplify():
            try:
                result[0] = simplify(diff)
            except Exception:
                result[0] = None

        t = threading.Thread(target=_simplify)
        t.start()
        t.join(timeout=2.0)

        if result[0] is not None:
            if result[0] == 0:
                return True
            if allow_constant_diff and not result[0].free_symbols:
                return True

        # Tier 2: trig simplification
        try:
            trig_diff = trigsimp(diff)
            if trig_diff == 0:
                return True
            if allow_constant_diff and not trig_diff.free_symbols:
                return True
        except Exception:
            pass

        # Tier 3: numerical evaluation
        return _numerical_check(a, b, allow_constant_diff)

    except Exception as exc:
        logger.debug('Expression equivalence check failed: %s', exc)
        return None


def _numerical_check(a, b, allow_constant_diff=False):
    """Evaluate both expressions at random points to check equivalence."""
    try:
        from sympy import N, Rational
        import random

        free_syms = list(a.free_symbols | b.free_symbols)
        if not free_syms:
            # Both are constants — compare numerically
            try:
                val_a = complex(N(a))
                val_b = complex(N(b))
                if allow_constant_diff:
                    return True  # any two constants differ by a constant
                return abs(val_a - val_b) < 1e-10
            except Exception:
                return None

        # Test at 5 random points
        test_points = []
        for _ in range(5):
            point = {}
            for sym in free_syms:
                # Avoid 0 (division), use values in [0.5, 3.0]
                point[sym] = Rational(random.randint(1, 6), 2)
            test_points.append(point)

        diffs = []
        for point in test_points:
            try:
                val_a = complex(N(a.subs(point)))
                val_b = complex(N(b.subs(point)))
                diffs.append(val_a - val_b)
            except Exception:
                return None

        if not diffs:
            return None

        if allow_constant_diff:
            # All diffs should be the same constant
            first = diffs[0]
            return all(abs(d - first) < 1e-8 for d in diffs)
        else:
            return all(abs(d) < 1e-8 for d in diffs)

    except Exception:
        return None

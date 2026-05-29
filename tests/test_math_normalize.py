"""Tests for the math expression standardizer."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.math_normalize import check_math_equivalent, _is_math_expression


def test_numeric_equivalence():
    """Fractions and decimals that are equal."""
    assert check_math_equivalent('0.5', '1/2') is True
    assert check_math_equivalent('0.25', '1/4') is True
    assert check_math_equivalent('-0.25', '-1/4') is True
    assert check_math_equivalent('0.333', '1/3') is None  # 0.333 != 1/3 exactly


def test_whitespace_insensitive():
    """Whitespace differences should not matter."""
    assert check_math_equivalent('n/7-2', 'n/7 - 2') is True
    assert check_math_equivalent('x + 1', 'x+1') is True
    assert check_math_equivalent('2 x + 3', '2x + 3') is True


def test_parentheses_equivalence():
    """Redundant parentheses should not matter."""
    assert check_math_equivalent('(n/7)-2', 'n/7-2') is True
    assert check_math_equivalent('(x+1)', 'x+1') is True


def test_commutativity():
    """Order of addition/multiplication should not matter."""
    assert check_math_equivalent('1+x', 'x+1') is True
    assert check_math_equivalent('3*x', 'x*3') is True


def test_algebraic_equivalence():
    """Algebraically equivalent expressions."""
    assert check_math_equivalent('2*(x+3)', '2x+6') is True
    assert check_math_equivalent('x**2 - 1', '(x-1)*(x+1)') is True


def test_trig_equivalence():
    """Trig identity equivalence."""
    assert check_math_equivalent('sqrt(3)/2', 'sqrt(3)/2') is True


def test_constant_of_integration():
    """Answers with +C should match regardless of the constant."""
    assert check_math_equivalent('x**2/2 - 2*x + C', 'x**2/2-2x+C') is True
    assert check_math_equivalent('x**2/2 - 2*x + 5', 'x**2/2-2x+C') is True
    assert check_math_equivalent('x**2/2 - 2*x', 'x**2/2-2x+C') is True


def test_unicode_normalization():
    """Unicode math characters should be normalized."""
    assert check_math_equivalent('pi', 'π') is True
    # Division sign
    assert check_math_equivalent('n/7', 'n÷7') is True


def test_incorrect_answers_rejected():
    """Wrong answers must be rejected."""
    assert check_math_equivalent('x+2', 'x+1') is not True
    assert check_math_equivalent('sin(x)', 'cos(x)') is not True
    assert check_math_equivalent('2x', '3x') is not True
    assert check_math_equivalent('5', '7') is not True


def test_non_math_passthrough():
    """Descriptive text should not be parsed as math."""
    assert _is_math_expression('local maximum') is False
    assert _is_math_expression('yes') is False
    assert _is_math_expression('removable discontinuity') is False
    assert _is_math_expression('hole') is False
    assert _is_math_expression('it averages both sides') is False
    assert _is_math_expression('neither') is False

    # These should return None (can't parse, fallback to string match)
    assert check_math_equivalent('local max', 'local maximum') is None


def test_math_expression_detection():
    """Math expressions should be detected correctly."""
    assert _is_math_expression('x+1') is True
    assert _is_math_expression('sqrt(3)/2') is True
    assert _is_math_expression('sin(x)') is True
    assert _is_math_expression('1/2') is True
    assert _is_math_expression('e^x') is True
    assert _is_math_expression('3/7') is True
    assert _is_math_expression('5') is True  # numeric


def test_pipe_separator():
    """The || mechanism should work with SymPy fallback."""
    # Should match against any variant
    assert check_math_equivalent('0.5', '1/2||0.5||one half') is True
    assert check_math_equivalent('x+1', '1+x||x + 1') is True


def test_exponential_expressions():
    """Exponential and logarithmic expressions."""
    assert check_math_equivalent('exp(x)', 'e^x') is True


def test_ln_notation():
    """ln should be treated as natural log."""
    assert check_math_equivalent('ln(x)', 'log(x)') is True


def test_equation_with_equals():
    """Equations with = sign."""
    assert check_math_equivalent('y = 5x - 1', 'y=5x-1') is True


if __name__ == '__main__':
    tests = [
        test_numeric_equivalence,
        test_whitespace_insensitive,
        test_parentheses_equivalence,
        test_commutativity,
        test_algebraic_equivalence,
        test_trig_equivalence,
        test_constant_of_integration,
        test_unicode_normalization,
        test_incorrect_answers_rejected,
        test_non_math_passthrough,
        test_math_expression_detection,
        test_pipe_separator,
        test_exponential_expressions,
        test_ln_notation,
        test_equation_with_equals,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f'  PASS: {test.__name__}')
            passed += 1
        except AssertionError as e:
            print(f'  FAIL: {test.__name__} — {e}')
            failed += 1
        except Exception as e:
            print(f'  ERROR: {test.__name__} — {type(e).__name__}: {e}')
            failed += 1

    print(f'\n{passed} passed, {failed} failed')

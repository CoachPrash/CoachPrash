import re


def wrap_in_main(student_code):
    """Wrap bare Java statements in a main method inside a Solution class."""
    return (
        'public class Solution {\n'
        '    public static void main(String[] args) {\n'
        f'        {student_code}\n'
        '    }\n'
        '}\n'
    )


def build_executable(student_code, test_harness):
    """Assemble a complete Java source file from student code + harness config.

    test_harness types:
      - output_match: wrap code in main(), compare stdout to expected
      - method_test: handled by test_runner.build_method_harness()
    """
    harness_type = test_harness.get('type', 'output_match')

    if harness_type == 'output_match':
        if test_harness.get('wrap_in_main', True):
            return wrap_in_main(student_code)
        return student_code

    # For method_test, the caller should use test_runner.build_method_harness()
    # and pass the result here as already-assembled code
    return student_code


def grade_output_match(actual_output, expected_output):
    """Compare actual stdout against expected output.

    Returns dict with: passed (bool), expected, actual, details.
    """
    actual_lines = actual_output.strip().splitlines()
    expected_lines = expected_output.strip().splitlines()

    passed = actual_lines == expected_lines

    details = []
    if not passed:
        max_lines = max(len(actual_lines), len(expected_lines))
        for i in range(max_lines):
            act = actual_lines[i] if i < len(actual_lines) else '<missing>'
            exp = expected_lines[i] if i < len(expected_lines) else '<extra>'
            if act != exp:
                details.append(f'Line {i + 1}: expected "{exp}", got "{act}"')

    return {
        'passed': passed,
        'expected': expected_output.strip(),
        'actual': actual_output.strip(),
        'details': details,
    }


def grade_test_cases(raw_output, test_cases):
    """Parse structured test output markers from stdout.

    Markers: @@TEST:N:PASS@@ or @@TEST:N:FAIL:expected=X:got=Y@@
             @@TEST:N:ERROR:message@@
             @@RESULTS:passed/total@@

    Returns dict with: passed, failed, errored, total, results[].
    """
    results = []
    test_pattern = re.compile(
        r'@@TEST:(\d+):(PASS|FAIL|ERROR)(?::(.+?))?@@'
    )

    for match in test_pattern.finditer(raw_output):
        case_num = int(match.group(1))
        status = match.group(2)
        detail_str = match.group(3) or ''

        # Build per-test result
        case_idx = case_num - 1
        description = ''
        if case_idx < len(test_cases):
            description = test_cases[case_idx].get('description', '')

        result = {
            'case_num': case_num,
            'status': status.lower(),
            'description': description,
        }

        if status == 'FAIL':
            parts = {}
            for kv in detail_str.split(':'):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    parts[k] = v
            result['expected'] = parts.get('expected', '')
            result['actual'] = parts.get('got', '')
        elif status == 'ERROR':
            result['error'] = detail_str

        results.append(result)

    passed = sum(1 for r in results if r['status'] == 'pass')
    failed = sum(1 for r in results if r['status'] == 'fail')
    errored = sum(1 for r in results if r['status'] == 'error')

    return {
        'passed': passed,
        'failed': failed,
        'errored': errored,
        'total': len(results),
        'results': results,
    }

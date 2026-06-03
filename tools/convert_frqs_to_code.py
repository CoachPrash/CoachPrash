"""Convert FRQ problems in the AP CSA JSON to 'code' type with test harnesses.

Phase 1: Convert output_match-style FRQs (ones with System.out.println in the answer).
Keeps manual_trace and explanation FRQs as 'frq' type (can't auto-grade).

Usage: python tools/convert_frqs_to_code.py
"""
import json
import re
import sys
import os

INPUT_FILE = os.path.join('content', 'computer-science_ap-cs-a-java.json')


def extract_code_from_html(html):
    """Extract Java code from <pre><code>...</code></pre> blocks."""
    match = re.search(r'<pre><code[^>]*>(.*?)</code></pre>', html, re.DOTALL)
    if match:
        code = match.group(1)
        # Unescape HTML entities
        code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        code = code.replace('&quot;', '"').replace('&#39;', "'")
        return code.strip()
    return None


def has_system_out(code):
    """Check if code uses System.out.println or System.out.print."""
    return bool(re.search(r'System\.out\.print', code))


def has_method_signature(code):
    """Check if code defines a method (public/private static/instance)."""
    return bool(re.search(r'(public|private|protected)\s+(static\s+)?\w+\s+\w+\s*\(', code))


def has_class_definition(code):
    """Check if code defines a class."""
    return bool(re.search(r'(public\s+)?class\s+\w+', code))


def is_trace_or_explanation(question_html, correct_answer):
    """Check if the problem is a manual trace or explanation (can't auto-grade)."""
    q_lower = (question_html or '').lower()
    a_lower = (correct_answer or '').lower()
    trace_keywords = ['trace', 'show the state', 'step-by-step', 'each pass']
    explain_keywords = ['explain', 'describe', 'what is the difference', 'in your own words']
    for kw in trace_keywords:
        if kw in q_lower or kw in a_lower:
            return True
    for kw in explain_keywords:
        if kw in q_lower:
            return True
    return False


def predict_output(code):
    """Try to predict what the code would print. Returns None if can't predict.
    This is a simplified approach — for complex code, we return None and skip conversion.
    """
    # For simple code with System.out.println, we can sometimes predict output
    # But this is fragile — better to let the user provide expected outputs manually
    return None


def convert_problem(problem):
    """Convert an FRQ problem to 'code' type if appropriate.
    Returns the modified problem dict, or None if no conversion needed.
    """
    if problem.get('problem_type') != 'frq':
        return None

    correct_answer = problem.get('correct_answer', '')
    question_html = problem.get('question_html', '')
    code = extract_code_from_html(correct_answer)

    if not code:
        return None

    # Skip traces and explanations
    if is_trace_or_explanation(question_html, correct_answer):
        return None

    # Determine harness type
    if has_class_definition(code) and not has_system_out(code):
        # Full class definition without output — needs class_test (Phase 3)
        return None

    if has_method_signature(code) and not has_system_out(code):
        # Method definition — needs method_test harness (Phase 2)
        # For now, convert the type but leave harness empty for Phase 2 to fill
        problem['problem_type'] = 'code'
        # Extract method name for starter_code
        method_match = re.search(
            r'((?:public|private|protected)\s+(?:static\s+)?\w+(?:<[^>]+>)?\s+(\w+)\s*\([^)]*\))',
            code
        )
        if method_match:
            signature = method_match.group(1)
            problem['starter_code'] = signature + ' {\n    // Your code here\n}'
        else:
            problem['starter_code'] = '// Write your method here\n'
        # Mark for Phase 2 — test_harness will be added when test_runner is ready
        problem['test_harness'] = {
            'type': 'method_test',
            'test_cases': [],  # To be filled in Phase 2
            '_needs_test_cases': True,
        }
        return problem

    if has_system_out(code):
        # Code that prints output — output_match
        problem['problem_type'] = 'code'

        # Check if it needs wrapping in main()
        needs_wrap = not re.search(r'public\s+static\s+void\s+main', code)

        if needs_wrap:
            problem['starter_code'] = '// Write your code below\n'
        else:
            # Has its own main — provide the class shell
            problem['starter_code'] = code.split('{', 1)[0] + '{\n    // Your code here\n}'

        problem['test_harness'] = {
            'type': 'output_match',
            'expected_output': '',  # MUST be filled manually
            'wrap_in_main': needs_wrap,
            '_needs_expected_output': True,
        }
        return problem

    # Default: can't auto-convert safely
    return None


def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    converted = 0
    skipped = 0
    needs_manual = []

    for topic in data.get('topics', []):
        for concept in topic.get('concepts', []):
            for ps in concept.get('problem_sets', []):
                for problem in ps.get('problems', []):
                    if problem.get('problem_type') != 'frq':
                        continue

                    result = convert_problem(problem)
                    if result:
                        converted += 1
                        if result.get('test_harness', {}).get('_needs_expected_output'):
                            needs_manual.append({
                                'concept': concept.get('title', ''),
                                'type': 'output_match',
                                'code': extract_code_from_html(result.get('correct_answer', '')),
                            })
                        elif result.get('test_harness', {}).get('_needs_test_cases'):
                            needs_manual.append({
                                'concept': concept.get('title', ''),
                                'type': 'method_test',
                                'code': extract_code_from_html(result.get('correct_answer', '')),
                            })
                    else:
                        skipped += 1

    # Write back
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'Converted: {converted} FRQ problems to code type')
    print(f'Skipped: {skipped} FRQ problems (traces/explanations/classes)')
    print()
    if needs_manual:
        print(f'{len(needs_manual)} problems need manual data:')
        for item in needs_manual:
            marker = 'expected_output' if item['type'] == 'output_match' else 'test_cases'
            print(f'  [{item["type"]}] {item["concept"]} — needs {marker}')


if __name__ == '__main__':
    main()

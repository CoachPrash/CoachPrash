"""Build Java test harness source code for method-level testing.

Generates a complete Java class that wraps student code + test runner
using structured output markers for reliable parsing.
"""


def _java_value_literal(value, type_name):
    """Convert a string value to a Java literal based on type."""
    if type_name == 'int':
        return value
    elif type_name == 'double':
        return value if '.' in value else value + '.0'
    elif type_name == 'boolean':
        return value.lower()
    elif type_name == 'String':
        return f'"{value}"'
    elif type_name == 'char':
        return f"'{value}'"
    elif type_name == 'int[]':
        # Value like "1,2,3" → new int[]{1, 2, 3}
        if not value or value.strip() == '':
            return 'new int[]{}'
        return 'new int[]{' + value + '}'
    elif type_name == 'String[]':
        if not value or value.strip() == '':
            return 'new String[]{}'
        items = ', '.join(f'"{v.strip()}"' for v in value.split(','))
        return 'new String[]{' + items + '}'
    elif type_name == 'ArrayList<Integer>':
        if not value or value.strip() == '':
            return 'new ArrayList<>()'
        return 'new ArrayList<>(java.util.Arrays.asList(' + value + '))'
    elif type_name == 'ArrayList<String>':
        if not value or value.strip() == '':
            return 'new ArrayList<>()'
        items = ', '.join(f'"{v.strip()}"' for v in value.split(','))
        return 'new ArrayList<>(java.util.Arrays.asList(' + items + '))'
    elif type_name == 'int[][]':
        # Value like "{{1,2},{3,4}}" — pass through as-is
        return 'new int[][]' + value
    else:
        return value


def build_method_harness(student_code, test_cases, class_name='Solution', method_name=''):
    """Build a complete Java source file with student code + test runner.

    Args:
        student_code: The student's Java code (method body)
        test_cases: List of test case dicts with keys:
            inputs, input_types, expected, description
        class_name: Class name to wrap code in
        method_name: The method to call in test cases

    Returns:
        Complete Java source string ready for compilation
    """
    if not test_cases:
        return f'public class {class_name} {{\n{student_code}\n}}'

    # Detect return type from first test case expected value and method signature
    # We infer based on test case structure
    total = len(test_cases)

    lines = []
    lines.append('import java.util.*;')
    lines.append('')
    lines.append(f'public class {class_name} {{')
    lines.append('')
    lines.append('    // --- Student code ---')
    lines.append(f'    {student_code}')
    lines.append('')
    lines.append('    // --- Test runner ---')
    lines.append('    public static void main(String[] args) {')
    lines.append(f'        int passed = 0;')
    lines.append(f'        int total = {total};')
    lines.append('')

    for i, tc in enumerate(test_cases):
        case_num = i + 1
        inputs = tc.get('inputs', [])
        input_types = tc.get('input_types', [])
        expected = tc.get('expected', '')
        call_name = method_name or tc.get('method_name', '')

        # Build method call arguments
        args = []
        for j, (val, typ) in enumerate(zip(inputs, input_types)):
            arg_var = f'arg{case_num}_{j}'
            literal = _java_value_literal(val, typ)
            lines.append(f'        {typ} {arg_var} = {literal};')
            args.append(arg_var)

        args_str = ', '.join(args)

        lines.append(f'        try {{')

        if expected == 'void':
            # Void method — just check it doesn't throw
            lines.append(f'            {call_name}({args_str});')
            lines.append(f'            passed++;')
            lines.append(f'            System.out.println("@@TEST:{case_num}:PASS@@");')
        else:
            lines.append(f'            var result{case_num} = {call_name}({args_str});')
            lines.append(f'            String actual{case_num} = String.valueOf(result{case_num});')
            lines.append(f'            if (actual{case_num}.equals("{expected}")) {{')
            lines.append(f'                passed++;')
            lines.append(f'                System.out.println("@@TEST:{case_num}:PASS@@");')
            lines.append(f'            }} else {{')
            lines.append(f'                System.out.println("@@TEST:{case_num}:FAIL:expected={expected}:got=" + actual{case_num} + "@@");')
            lines.append(f'            }}')

        lines.append(f'        }} catch (Exception e) {{')
        lines.append(f'            System.out.println("@@TEST:{case_num}:ERROR:" + e.getClass().getSimpleName() + ": " + e.getMessage() + "@@");')
        lines.append(f'        }}')
        lines.append('')

    lines.append(f'        System.out.println("@@RESULTS:" + passed + "/" + total + "@@");')
    lines.append('    }')
    lines.append('}')

    return '\n'.join(lines)

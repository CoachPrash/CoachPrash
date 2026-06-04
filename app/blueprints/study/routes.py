import logging
from datetime import datetime, timezone
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.blueprints.study import study_bp
from app.models.practice import Problem, Choice, Hint, StepByStepSolution
from app.models.progress import StudentProgress, AttemptLog
from app.utils.access import can_access_hint, can_access_solution
from app.utils.progress import compute_student_stats
from app.extensions import db, limiter

logger = logging.getLogger(__name__)


# --- Practice API Endpoints ---

@study_bp.route('/api/practice/check', methods=['POST'])
@limiter.limit('60/minute')
def check_answer():
    data = request.get_json()
    if not data or 'problem_id' not in data or 'submitted_answer' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    problem = db.session.get(Problem, data['problem_id'])
    if not problem:
        return jsonify({'error': 'Problem not found'}), 404

    submitted = data['submitted_answer'].strip()
    is_correct = False
    correct_display = ''

    if problem.problem_type == 'mcq':
        correct_choice = Choice.query.filter_by(
            problem_id=problem.id, is_correct=True
        ).first()
        if correct_choice:
            is_correct = (submitted == correct_choice.id)
            correct_display = correct_choice.choice_text
    elif problem.problem_type == 'frq':
        # FRQ: no auto-grading — always accept the submission
        is_correct = None
        correct_display = problem.correct_answer or ''
    else:
        # Fill-in-blank: case-insensitive string match first, then SymPy fallback
        accepted = [a.strip().lower() for a in (problem.correct_answer or '').split('||')]
        is_correct = submitted.lower() in accepted
        correct_display = (problem.correct_answer or '').split('||')[0].strip()

        if not is_correct:
            from app.utils.math_normalize import check_math_equivalent
            math_result = check_math_equivalent(submitted, problem.correct_answer or '')
            if math_result is True:
                is_correct = True

    # Log attempt for authenticated users
    if current_user.is_authenticated:
        attempt = AttemptLog(
            student_id=current_user.id,
            problem_id=problem.id,
            submitted_answer=submitted,
            is_correct=bool(is_correct) if is_correct is not None else False,
            hints_used=data.get('hints_used', 0),
            time_spent_seconds=data.get('time_spent_seconds'),
        )
        db.session.add(attempt)
        db.session.commit()

    result = {'correct': is_correct}
    if is_correct is None:
        # FRQ: return model answer for display
        result['model_answer'] = correct_display
    elif not is_correct:
        result['correct_answer'] = correct_display
    return jsonify(result)


@study_bp.route('/api/practice/run-code', methods=['POST'])
@limiter.limit('10/minute')
def run_code():
    """Execute student Java code and grade against test harness."""
    data = request.get_json()
    if not data or 'problem_id' not in data or 'code' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    problem = db.session.get(Problem, data['problem_id'])
    if not problem or problem.problem_type != 'code':
        return jsonify({'error': 'Problem not found'}), 404

    code = data['code'].strip()
    if not code:
        return jsonify({'error': 'No code submitted'}), 400

    from app.utils.onecompiler import (
        execute_java, check_forbidden,
        CodeTooLongError, ForbiddenCodeError, QuotaExceededError, OneCompilerError,
    )
    from app.utils.code_grader import build_executable, grade_output_match, grade_test_cases

    # Security check
    try:
        check_forbidden(code)
    except ForbiddenCodeError as e:
        return jsonify({'compile_error': True, 'error': str(e)})

    harness = problem.test_harness or {}
    harness_type = harness.get('type', 'output_match')

    # Build executable source
    if harness_type == 'method_test':
        from app.utils.test_runner import build_method_harness
        source = build_method_harness(
            code,
            harness.get('test_cases', []),
            class_name=harness.get('class_name', 'Solution'),
            method_name=harness.get('method_name', ''),
        )
    else:
        source = build_executable(code, harness)

    # Execute via OneCompiler
    try:
        result = execute_java(source)
    except CodeTooLongError as e:
        return jsonify({'compile_error': True, 'error': str(e)})
    except QuotaExceededError:
        return jsonify({'error': 'Code execution service temporarily unavailable. Please try again later.'}), 503
    except OneCompilerError as e:
        return jsonify({'error': str(e)}), 500

    # Check for compilation/runtime errors
    if result['status'] != 'success':
        error_text = result['stderr'] or result['error'] or 'Unknown error'
        is_compile = 'error:' in error_text.lower() and 'exception' not in error_text.lower()
        if is_compile:
            response = {'compile_error': True, 'error': error_text}
        else:
            response = {'runtime_error': True, 'error': error_text}

        # Log attempt
        if current_user.is_authenticated:
            attempt = AttemptLog(
                student_id=current_user.id,
                problem_id=problem.id,
                submitted_answer=code[:2000],
                is_correct=False,
            )
            db.session.add(attempt)
            db.session.commit()

        return jsonify(response)

    # Grade the output
    if harness_type == 'method_test':
        test_results = grade_test_cases(result['stdout'], harness.get('test_cases', []))
        is_correct = test_results['passed'] == test_results['total'] and test_results['total'] > 0
        response = {
            'test_results': test_results,
            'output': result['stdout'],
        }
    else:
        expected = harness.get('expected_output', '')
        logger.info('run-code output_match: stdout=%r, expected=%r', result['stdout'], expected)
        grade = grade_output_match(result['stdout'], expected)
        is_correct = grade['passed']
        response = {
            'passed': grade['passed'],
            'expected': grade['expected'],
            'actual': grade['actual'],
            'details': grade['details'],
            'output': result['stdout'],
        }

    # Log attempt
    if current_user.is_authenticated:
        attempt = AttemptLog(
            student_id=current_user.id,
            problem_id=problem.id,
            submitted_answer=code[:2000],
            is_correct=is_correct,
        )
        db.session.add(attempt)
        db.session.commit()

    return jsonify(response)


@study_bp.route('/api/practice/hint', methods=['POST'])
@limiter.limit('60/minute')
def get_hint():
    data = request.get_json()
    if not data or 'problem_id' not in data:
        return jsonify({'error': 'Missing problem_id'}), 400

    hint_index = data.get('hint_index', 0)

    # Freemium gating
    if not can_access_hint(current_user, hint_index):
        return jsonify({'blocked': True, 'reason': 'premium_required'})

    hint = Hint.query.filter_by(
        problem_id=data['problem_id']
    ).order_by(Hint.display_order).offset(hint_index).first()

    if not hint:
        return jsonify({'error': 'No more hints available'}), 404

    total_hints = Hint.query.filter_by(problem_id=data['problem_id']).count()
    has_more = (hint_index + 1) < total_hints

    # Check if next hint is accessible
    next_accessible = has_more and can_access_hint(current_user, hint_index + 1)

    from app.utils.bucket_filter import resolve_bucket_keys_str
    return jsonify({
        'hint_text': resolve_bucket_keys_str(hint.hint_text),
        'has_more': has_more,
        'next_accessible': next_accessible,
    })


@study_bp.route('/api/practice/solution', methods=['POST'])
@limiter.limit('60/minute')
def get_solution():
    data = request.get_json()
    if not data or 'problem_id' not in data:
        return jsonify({'error': 'Missing problem_id'}), 400

    if not can_access_solution(current_user):
        return jsonify({'blocked': True, 'reason': 'premium_required'})

    solution = StepByStepSolution.query.filter_by(
        problem_id=data['problem_id']
    ).first()

    if not solution:
        return jsonify({'error': 'No solution available'}), 404

    from app.utils.bucket_filter import resolve_bucket_keys_str
    steps = solution.steps_json
    if steps and isinstance(steps, list):
        steps = [
            {**s, 'text': resolve_bucket_keys_str(s.get('text', ''))}
            if isinstance(s, dict) else s
            for s in steps
        ]
    return jsonify({'steps': steps})


@study_bp.route('/api/practice/complete', methods=['POST'])
@limiter.limit('60/minute')
def complete_quiz():
    """Called by JS when a quiz is finished. Updates StudentProgress."""
    if not current_user.is_authenticated:
        return jsonify({'saved': False, 'reason': 'not_authenticated'})

    data = request.get_json()
    if not data or 'concept_id' not in data:
        return jsonify({'error': 'Missing concept_id'}), 400

    score = data.get('score', 0)
    total = data.get('total', 1)
    mastery = score / total if total > 0 else 0

    progress = StudentProgress.query.filter_by(
        student_id=current_user.id,
        concept_id=data['concept_id'],
    ).first()

    if not progress:
        progress = StudentProgress(
            student_id=current_user.id,
            concept_id=data['concept_id'],
        )
        db.session.add(progress)

    progress.mastery_score = mastery
    progress.last_accessed = datetime.now(timezone.utc)
    if mastery >= 0.7:
        progress.status = 'completed'
    elif progress.status == 'not_started':
        progress.status = 'in_progress'

    db.session.commit()
    logger.info('Quiz completed: student=%s, concept=%s, mastery=%.2f, status=%s',
                current_user.id, data['concept_id'], mastery, progress.status)
    return jsonify({'saved': True, 'status': progress.status, 'mastery': mastery})


# --- Progress Dashboard ---

@study_bp.route('/progress/')
@login_required
def progress_dashboard():
    stats = compute_student_stats(current_user.id)
    return render_template(
        'progress/dashboard.html',
        is_premium=current_user.is_premium,
        **stats,
    )

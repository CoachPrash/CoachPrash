import logging
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.extensions import db, limiter
from app.models.user import User
from app.models.parent import ParentStudentLink, ParentLinkCode
from app.models.progress import StudentProgress, AttemptLog
from app.models.content import Subject, Concept
from app.models.practice import Problem
from app.blueprints.parent import parent_bp
from app.blueprints.parent.forms import LinkCodeForm

logger = logging.getLogger(__name__)


def parent_required(f):
    """Decorator that requires the current user to be a parent."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_parent:
            logger.warning('Unauthorized parent access attempt by %s (id=%s)',
                           current_user.username, current_user.id)
            abort(403)
        return f(*args, **kwargs)
    return decorated


@parent_bp.route('/')
@parent_required
def dashboard():
    links = ParentStudentLink.query.filter_by(parent_id=current_user.id).all()

    children = []
    for link in links:
        student = db.session.get(User, link.student_id)
        if not student:
            continue

        total_completed = StudentProgress.query.filter_by(
            student_id=student.id, status='completed'
        ).count()

        total_attempts = AttemptLog.query.filter_by(student_id=student.id).count()
        correct = AttemptLog.query.filter_by(student_id=student.id, is_correct=True).count()
        accuracy = round((correct / total_attempts * 100), 1) if total_attempts > 0 else 0

        last_attempt = AttemptLog.query.filter_by(student_id=student.id)\
            .order_by(AttemptLog.attempted_at.desc()).first()

        children.append({
            'student': student,
            'link': link,
            'total_completed': total_completed,
            'total_attempts': total_attempts,
            'accuracy': accuracy,
            'last_active': last_attempt.attempted_at if last_attempt else None,
        })

    return render_template('parent/dashboard.html', children=children)


@parent_bp.route('/student/<student_id>')
@parent_required
def student_progress(student_id):
    # Verify ownership
    link = ParentStudentLink.query.filter_by(
        parent_id=current_user.id, student_id=student_id
    ).first()
    if not link:
        logger.warning('Parent %s attempted to access unlinked student %s',
                       current_user.id, student_id)
        abort(403)

    student = db.session.get(User, student_id)
    if not student:
        abort(404)

    # Aggregate stats (same logic as study.progress_dashboard)
    total_completed = StudentProgress.query.filter_by(
        student_id=student.id, status='completed'
    ).count()

    total_in_progress = StudentProgress.query.filter_by(
        student_id=student.id, status='in_progress'
    ).count()

    total_attempts = AttemptLog.query.filter_by(student_id=student.id).count()
    correct_attempts = AttemptLog.query.filter_by(student_id=student.id, is_correct=True).count()
    accuracy = round((correct_attempts / total_attempts * 100), 1) if total_attempts > 0 else 0

    # Study streak
    streak = 0
    if total_attempts > 0:
        today = datetime.now(timezone.utc).date()
        check_date = today
        while True:
            day_start = datetime.combine(check_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            has_activity = AttemptLog.query.filter(
                AttemptLog.student_id == student.id,
                AttemptLog.attempted_at >= day_start,
                AttemptLog.attempted_at < day_end,
            ).first() is not None
            if has_activity:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

    # Per-subject progress
    subject_progress = []
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.display_order).all()
    for subj in subjects:
        topic_ids = [t.id for t in subj.topics.filter_by(is_active=True).all()]
        if not topic_ids:
            continue
        total_concepts = Concept.query.filter(
            Concept.topic_id.in_(topic_ids), Concept.is_active == True  # noqa: E712
        ).count()
        if total_concepts == 0:
            continue
        completed = StudentProgress.query.join(Concept).filter(
            StudentProgress.student_id == student.id,
            StudentProgress.status == 'completed',
            Concept.topic_id.in_(topic_ids),
        ).count()
        subject_progress.append({
            'subject': subj,
            'total': total_concepts,
            'completed': completed,
            'pct': round(completed / total_concepts * 100) if total_concepts > 0 else 0,
        })

    # Filter to subjects with interaction
    subject_progress = [sp for sp in subject_progress if sp['completed'] > 0 or
                        StudentProgress.query.join(Concept).filter(
                            StudentProgress.student_id == student.id,
                            Concept.topic_id.in_([t.id for t in sp['subject'].topics.all()]),
                        ).first() is not None]

    # Recent activity
    recent_attempts = AttemptLog.query.filter_by(
        student_id=student.id
    ).order_by(AttemptLog.attempted_at.desc()).limit(20).all()

    recent_activity = []
    for attempt in recent_attempts:
        problem = db.session.get(Problem, attempt.problem_id)
        if problem and problem.problem_set:
            concept = db.session.get(Concept, problem.problem_set.concept_id)
            recent_activity.append({
                'attempt': attempt,
                'problem': problem,
                'concept': concept,
            })

    return render_template(
        'parent/student_progress.html',
        student=student,
        total_completed=total_completed,
        total_in_progress=total_in_progress,
        total_attempts=total_attempts,
        accuracy=accuracy,
        streak=streak,
        subject_progress=subject_progress,
        recent_activity=recent_activity,
        is_premium=student.is_premium,
    )


@parent_bp.route('/link', methods=['GET', 'POST'])
@login_required
@limiter.limit("5/minute", methods=["POST"])
def link_student():
    form = LinkCodeForm()

    if form.validate_on_submit():
        code_str = form.code.data.strip().upper()
        link_code = ParentLinkCode.query.filter_by(code=code_str).first()

        if not link_code:
            logger.warning('Invalid link code attempt by %s: %s', current_user.username, code_str)
            flash('Invalid link code. Please check and try again.', 'danger')
            return render_template('parent/link_student.html', form=form)

        if not link_code.is_valid():
            logger.warning('Expired/used link code attempt by %s: %s', current_user.username, code_str)
            if link_code.is_used:
                flash('This link code has already been used.', 'danger')
            else:
                flash('This link code has expired. Please ask your admin for a new one.', 'danger')
            return render_template('parent/link_student.html', form=form)

        # Check if already linked
        existing = ParentStudentLink.query.filter_by(
            parent_id=current_user.id, student_id=link_code.student_id
        ).first()
        if existing:
            flash('You are already linked to this student.', 'info')
            return redirect(url_for('parent.dashboard'))

        # Can't link to yourself
        if link_code.student_id == current_user.id:
            flash('You cannot link to your own account.', 'danger')
            return render_template('parent/link_student.html', form=form)

        # Create the link
        new_link = ParentStudentLink(
            parent_id=current_user.id,
            student_id=link_code.student_id,
        )
        db.session.add(new_link)

        # Mark code as used
        link_code.is_used = True
        link_code.used_by = current_user.id

        # Upgrade role to parent if currently a student
        if current_user.role == 'student':
            current_user.role = 'parent'
            logger.info('User %s role upgraded to parent', current_user.username)

        db.session.commit()

        student = db.session.get(User, link_code.student_id)
        logger.info('Parent-student link created: parent=%s, student=%s, code=%s',
                    current_user.username, student.username, code_str)
        flash(f'Successfully linked to {student.username}!', 'success')
        return redirect(url_for('parent.dashboard'))

    return render_template('parent/link_student.html', form=form)

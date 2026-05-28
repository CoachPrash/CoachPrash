"""Shared student progress computation used by study, parent, and coach dashboards."""
import logging
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.progress import StudentProgress, AttemptLog
from app.models.content import Subject, Course, Topic, Concept, TopicConcept
from app.models.practice import Problem

logger = logging.getLogger(__name__)


def compute_student_stats(student_id):
    """Compute aggregate stats for a student.

    Returns dict with: total_completed, total_in_progress, total_attempts,
    accuracy, streak, subject_progress, recent_activity.
    """
    total_completed = StudentProgress.query.filter_by(
        student_id=student_id, status='completed'
    ).count()

    total_in_progress = StudentProgress.query.filter_by(
        student_id=student_id, status='in_progress'
    ).count()

    total_attempts = AttemptLog.query.filter_by(student_id=student_id).count()
    correct_attempts = AttemptLog.query.filter_by(
        student_id=student_id, is_correct=True
    ).count()
    accuracy = round((correct_attempts / total_attempts * 100), 1) if total_attempts > 0 else 0

    # Study streak: consecutive days with at least 1 attempt
    streak = 0
    if total_attempts > 0:
        today = datetime.now(timezone.utc).date()
        check_date = today
        while True:
            day_start = datetime.combine(check_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            has_activity = AttemptLog.query.filter(
                AttemptLog.student_id == student_id,
                AttemptLog.attempted_at >= day_start,
                AttemptLog.attempted_at < day_end,
            ).first() is not None
            if has_activity:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

    # Per-subject progress (via TopicConcept join)
    subject_progress = []
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.display_order).all()
    for subj in subjects:
        topic_ids = []
        for course in subj.courses.filter_by(is_active=True).all():
            topic_ids.extend(t.id for t in Topic.query.filter_by(course_id=course.id, is_active=True).all())
        if not topic_ids:
            continue
        concept_ids = [
            tc.concept_id for tc in TopicConcept.query.filter(
                TopicConcept.topic_id.in_(topic_ids)
            ).all()
        ]
        concept_ids = list(set(concept_ids))
        if not concept_ids:
            continue
        total_concepts = Concept.query.filter(
            Concept.id.in_(concept_ids), Concept.is_active == True  # noqa: E712
        ).count()
        if total_concepts == 0:
            continue
        completed = StudentProgress.query.filter(
            StudentProgress.student_id == student_id,
            StudentProgress.status == 'completed',
            StudentProgress.concept_id.in_(concept_ids),
        ).count()
        has_interaction = completed > 0 or StudentProgress.query.filter(
            StudentProgress.student_id == student_id,
            StudentProgress.concept_id.in_(concept_ids),
        ).first() is not None
        if has_interaction:
            subject_progress.append({
                'subject': subj,
                'total': total_concepts,
                'completed': completed,
                'pct': round(completed / total_concepts * 100) if total_concepts > 0 else 0,
            })

    # Recent activity
    recent_attempts = AttemptLog.query.filter_by(
        student_id=student_id
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

    return {
        'total_completed': total_completed,
        'total_in_progress': total_in_progress,
        'total_attempts': total_attempts,
        'accuracy': accuracy,
        'streak': streak,
        'subject_progress': subject_progress,
        'recent_activity': recent_activity,
    }

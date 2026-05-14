from datetime import datetime, timezone
from flask import render_template
from flask_login import current_user
from app.blueprints.subjects import subjects_bp
from app.models.content import Subject, Topic, Concept
from app.models.practice import ProblemSet, Problem
from app.models.progress import StudentProgress
from app.utils.access import can_access_concept
from app.extensions import db


@subjects_bp.route('/')
def catalog():
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.display_order).all()
    return render_template('subjects/catalog.html', subjects=subjects)


@subjects_bp.route('/<slug>')
def topic_list(slug):
    subject = Subject.query.filter_by(slug=slug, is_active=True).first_or_404()
    topics = Topic.query.filter_by(
        subject_id=subject.id, is_active=True
    ).order_by(Topic.display_order).all()
    return render_template('subjects/topic_list.html', subject=subject, topics=topics)


@subjects_bp.route('/<subject_slug>/<topic_slug>')
def topic_detail(subject_slug, topic_slug):
    subject = Subject.query.filter_by(slug=subject_slug, is_active=True).first_or_404()
    topic = Topic.query.filter_by(
        subject_id=subject.id, slug=topic_slug, is_active=True
    ).first_or_404()
    concepts = topic.concepts.filter_by(is_active=True).order_by('display_order').all()

    # Build progress map for authenticated premium users
    progress_map = {}
    if current_user.is_authenticated and current_user.is_premium:
        concept_ids = [c.id for c in concepts]
        if concept_ids:
            records = StudentProgress.query.filter(
                StudentProgress.student_id == current_user.id,
                StudentProgress.concept_id.in_(concept_ids),
            ).all()
            progress_map = {r.concept_id: r for r in records}

    return render_template(
        'study/topic_overview.html',
        subject=subject,
        topic=topic,
        concepts=concepts,
        progress_map=progress_map,
    )


@subjects_bp.route('/<subject_slug>/<topic_slug>/<concept_slug>')
def concept_detail(subject_slug, topic_slug, concept_slug):
    subject = Subject.query.filter_by(slug=subject_slug, is_active=True).first_or_404()
    topic = Topic.query.filter_by(
        subject_id=subject.id, slug=topic_slug, is_active=True
    ).first_or_404()
    concept = Concept.query.filter_by(
        topic_id=topic.id, slug=concept_slug, is_active=True
    ).first_or_404()

    # Check freemium access
    show_teaser = not can_access_concept(current_user, concept)

    # Get all concepts in this topic for prev/next navigation
    all_concepts = topic.concepts.filter_by(is_active=True).order_by('display_order').all()
    current_index = next((i for i, c in enumerate(all_concepts) if c.id == concept.id), 0)
    prev_concept = all_concepts[current_index - 1] if current_index > 0 else None
    next_concept = all_concepts[current_index + 1] if current_index < len(all_concepts) - 1 else None

    # Check if concept has practice problems
    has_practice = ProblemSet.query.filter_by(
        concept_id=concept.id, is_active=True
    ).first() is not None

    # Update progress for authenticated premium users
    if current_user.is_authenticated and current_user.is_premium and not show_teaser:
        progress = StudentProgress.query.filter_by(
            student_id=current_user.id,
            concept_id=concept.id,
        ).first()
        if not progress:
            progress = StudentProgress(
                student_id=current_user.id,
                concept_id=concept.id,
                status='in_progress',
                last_accessed=datetime.now(timezone.utc),
            )
            db.session.add(progress)
            db.session.commit()
        elif progress.status == 'not_started':
            progress.status = 'in_progress'
            progress.last_accessed = datetime.now(timezone.utc)
            db.session.commit()
        else:
            progress.last_accessed = datetime.now(timezone.utc)
            db.session.commit()

    return render_template(
        'study/concept_detail.html',
        subject=subject,
        topic=topic,
        concept=concept,
        prev_concept=prev_concept,
        next_concept=next_concept,
        has_practice=has_practice,
        show_teaser=show_teaser,
    )


@subjects_bp.route('/<subject_slug>/<topic_slug>/<concept_slug>/practice/')
def practice_page(subject_slug, topic_slug, concept_slug):
    subject = Subject.query.filter_by(slug=subject_slug, is_active=True).first_or_404()
    topic = Topic.query.filter_by(
        subject_id=subject.id, slug=topic_slug, is_active=True
    ).first_or_404()
    concept = Concept.query.filter_by(
        topic_id=topic.id, slug=concept_slug, is_active=True
    ).first_or_404()

    # Get the first active problem set for this concept
    problem_set = ProblemSet.query.filter_by(
        concept_id=concept.id, is_active=True
    ).order_by(ProblemSet.display_order).first()

    if not problem_set:
        return render_template(
            'study/practice.html',
            subject=subject, topic=topic, concept=concept,
            problem_set=None, problems_json='[]',
            total_problems=0, is_premium=False,
        )

    # Load problems ordered by display_order
    problems = Problem.query.filter_by(
        problem_set_id=problem_set.id
    ).order_by(Problem.display_order).all()

    # Determine user tier
    is_premium = current_user.is_authenticated and current_user.is_premium
    total_available = len(problems)

    # Apply freemium gating: free users get first 3
    if not is_premium:
        problems = problems[:3]

    # Serialize problems for the client — NEVER include correct answers
    problems_data = []
    for p in problems:
        pdata = {
            'id': p.id,
            'question_html': p.question_html,
            'problem_type': p.problem_type,
            'difficulty': p.difficulty,
            'points': p.points,
        }
        if p.problem_type == 'mcq':
            choices = p.choices.order_by('display_order').all()
            pdata['choices'] = [
                {'id': c.id, 'text': c.choice_text}
                for c in choices
            ]
        pdata['hint_count'] = p.hints.count()
        pdata['has_solution'] = p.solution is not None
        problems_data.append(pdata)

    import json
    problems_json = json.dumps(problems_data)

    return render_template(
        'study/practice.html',
        subject=subject,
        topic=topic,
        concept=concept,
        problem_set=problem_set,
        problems_json=problems_json,
        total_problems=len(problems),
        total_available=total_available,
        is_premium=is_premium,
    )

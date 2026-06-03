from datetime import datetime, timezone
from flask import render_template, url_for
from flask_login import current_user
from app.blueprints.subjects import subjects_bp
from app.models.content import Subject, Course, Topic, Concept, TopicConcept
from app.models.practice import ProblemSet, Problem
from app.models.resource import Resource
from app.models.progress import StudentProgress
from app.utils.access import can_access_concept
from app.extensions import db


@subjects_bp.route('/')
def catalog():
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.display_order).all()
    return render_template('subjects/catalog.html', subjects=subjects)


@subjects_bp.route('/<slug>')
def course_list(slug):
    subject = Subject.query.filter_by(slug=slug, is_active=True).first_or_404()
    courses = Course.query.filter_by(
        subject_id=subject.id, is_active=True
    ).order_by(Course.display_order).all()

    # Build per-course stats
    courses_data = []
    total_concepts = 0
    total_minutes = 0

    for course in courses:
        course_topics = Topic.query.filter_by(course_id=course.id, is_active=True).all()
        concept_count = 0
        course_minutes = 0
        concept_ids = []

        for topic in course_topics:
            links = TopicConcept.query.join(Concept).filter(
                TopicConcept.topic_id == topic.id,
                Concept.is_active == True,
            ).all()
            for link in links:
                if link.concept_id not in concept_ids:
                    concept_ids.append(link.concept_id)
                    concept_count += 1
                    course_minutes += link.concept.estimated_minutes

        total_concepts += concept_count
        total_minutes += course_minutes

        # Per-course progress
        course_progress = None
        if current_user.is_authenticated and concept_ids:
            records = StudentProgress.query.filter(
                StudentProgress.student_id == current_user.id,
                StudentProgress.concept_id.in_(concept_ids),
            ).all()
            completed = sum(1 for r in records if r.status in ('completed', 'mastered'))
            course_progress = {
                'completed': completed,
                'total': concept_count,
                'percent': round(completed / concept_count * 100) if concept_count else 0,
            }

        courses_data.append({
            'course': course,
            'topic_count': len(course_topics),
            'concept_count': concept_count,
            'minutes': course_minutes,
            'progress': course_progress,
        })

    subject_resources = subject.resources.filter_by(is_active=True).order_by(Resource.display_order).all()

    return render_template(
        'subjects/course_home.html',
        subject=subject,
        courses_data=courses_data,
        subject_resources=subject_resources,
        total_concepts=total_concepts,
        total_minutes=total_minutes,
    )


@subjects_bp.route('/<subject_slug>/<course_slug>')
def course_detail(subject_slug, course_slug):
    subject = Subject.query.filter_by(slug=subject_slug, is_active=True).first_or_404()
    course = Course.query.filter_by(
        subject_id=subject.id, slug=course_slug, is_active=True
    ).first_or_404()

    topics = Topic.query.filter_by(
        course_id=course.id, is_active=True
    ).order_by(Topic.display_order).all()

    # Build per-topic concept counts and progress data
    topics_data = []
    total_concepts = 0
    total_minutes = 0
    total_problem_sets = 0

    for topic in topics:
        links = TopicConcept.query.join(Concept).filter(
            TopicConcept.topic_id == topic.id,
            Concept.is_active == True,
        ).order_by(TopicConcept.display_order).all()
        concept_count = len(links)
        total_concepts += concept_count
        topic_minutes = sum(link.concept.estimated_minutes for link in links)
        total_minutes += topic_minutes

        ps_count = 0
        concept_ids = []
        for link in links:
            concept_ids.append(link.concept_id)
            ps_count += ProblemSet.query.filter_by(
                concept_id=link.concept_id, is_active=True
            ).count()
        total_problem_sets += ps_count

        # Per-topic progress for logged-in students
        topic_progress = None
        if current_user.is_authenticated and concept_ids:
            records = StudentProgress.query.filter(
                StudentProgress.student_id == current_user.id,
                StudentProgress.concept_id.in_(concept_ids),
            ).all()
            completed = sum(1 for r in records if r.status in ('completed', 'mastered'))
            topic_progress = {
                'completed': completed,
                'total': concept_count,
                'percent': round(completed / concept_count * 100) if concept_count else 0,
            }

        topics_data.append({
            'topic': topic,
            'concept_count': concept_count,
            'minutes': topic_minutes,
            'problem_sets': ps_count,
            'progress': topic_progress,
        })

    # Overall course progress
    progress_summary = None
    if current_user.is_authenticated and total_concepts > 0:
        all_concept_ids = []
        for td in topics_data:
            for link in TopicConcept.query.filter_by(topic_id=td['topic'].id).all():
                if link.concept_id not in all_concept_ids:
                    all_concept_ids.append(link.concept_id)
        if all_concept_ids:
            all_progress = StudentProgress.query.filter(
                StudentProgress.student_id == current_user.id,
                StudentProgress.concept_id.in_(all_concept_ids),
            ).all()
            completed = sum(1 for r in all_progress if r.status in ('completed', 'mastered'))
            in_progress = sum(1 for r in all_progress if r.status == 'in_progress')
            progress_summary = {
                'completed': completed,
                'in_progress': in_progress,
                'total': total_concepts,
                'percent': round(completed / total_concepts * 100) if total_concepts else 0,
            }

    course_info = course.course_info or {}
    course_resources = course.resources.filter_by(is_active=True).order_by(Resource.display_order).all()

    return render_template(
        'study/course_overview.html',
        subject=subject,
        course=course,
        course_info=course_info,
        topics_data=topics_data,
        course_resources=course_resources,
        total_concepts=total_concepts,
        total_minutes=total_minutes,
        total_problem_sets=total_problem_sets,
        progress_summary=progress_summary,
    )


@subjects_bp.route('/<subject_slug>/<course_slug>/<topic_slug>')
def topic_detail(subject_slug, course_slug, topic_slug):
    subject = Subject.query.filter_by(slug=subject_slug, is_active=True).first_or_404()
    course = Course.query.filter_by(
        subject_id=subject.id, slug=course_slug, is_active=True
    ).first_or_404()
    topic = Topic.query.filter_by(
        course_id=course.id, slug=topic_slug, is_active=True
    ).first_or_404()

    # Get concepts via TopicConcept
    links = TopicConcept.query.join(Concept).filter(
        TopicConcept.topic_id == topic.id,
        Concept.is_active == True,
    ).order_by(TopicConcept.display_order).all()
    concepts = [link.concept for link in links]

    # Topic-level resources
    resources = topic.resources.filter_by(is_active=True).order_by(Resource.display_order).all()

    # Build progress map for authenticated users
    progress_map = {}
    if current_user.is_authenticated:
        concept_ids = [c.id for c in concepts]
        if concept_ids:
            records = StudentProgress.query.filter(
                StudentProgress.student_id == current_user.id,
                StudentProgress.concept_id.in_(concept_ids),
            ).all()
            progress_map = {r.concept_id: r for r in records}

    # Per-topic progress
    topic_progress = None
    if concepts:
        completed = sum(1 for c in concepts if progress_map.get(c.id) and progress_map[c.id].status in ('completed', 'mastered'))
        topic_progress = {
            'completed': completed,
            'total': len(concepts),
            'percent': round(completed / len(concepts) * 100) if concepts else 0,
        }

    # Prev/next topic navigation
    all_topics = Topic.query.filter_by(
        course_id=course.id, is_active=True
    ).order_by(Topic.display_order).all()
    current_index = next((i for i, t in enumerate(all_topics) if t.id == topic.id), 0)
    prev_topic = all_topics[current_index - 1] if current_index > 0 else None
    next_topic = all_topics[current_index + 1] if current_index < len(all_topics) - 1 else None

    return render_template(
        'study/topic_overview.html',
        subject=subject,
        course=course,
        topic=topic,
        concepts=concepts,
        resources=resources,
        progress_map=progress_map,
        topic_progress=topic_progress,
        prev_topic=prev_topic,
        next_topic=next_topic,
    )


@subjects_bp.route('/<subject_slug>/<course_slug>/<topic_slug>/<concept_slug>')
def concept_detail(subject_slug, course_slug, topic_slug, concept_slug):
    subject = Subject.query.filter_by(slug=subject_slug, is_active=True).first_or_404()
    course = Course.query.filter_by(
        subject_id=subject.id, slug=course_slug, is_active=True
    ).first_or_404()
    topic = Topic.query.filter_by(
        course_id=course.id, slug=topic_slug, is_active=True
    ).first_or_404()

    # Look up concept through TopicConcept
    link = TopicConcept.query.join(Concept).filter(
        TopicConcept.topic_id == topic.id,
        Concept.slug == concept_slug,
        Concept.is_active == True,
    ).first_or_404()
    concept = link.concept

    # Check freemium access
    show_teaser = not can_access_concept(current_user, concept)

    # Get all concepts in this topic for prev/next navigation
    all_links = TopicConcept.query.join(Concept).filter(
        TopicConcept.topic_id == topic.id,
        Concept.is_active == True,
    ).order_by(TopicConcept.display_order).all()
    all_concepts = [l.concept for l in all_links]
    current_index = next((i for i, c in enumerate(all_concepts) if c.id == concept.id), 0)
    prev_concept = all_concepts[current_index - 1] if current_index > 0 else None
    next_concept = all_concepts[current_index + 1] if current_index < len(all_concepts) - 1 else None

    # Check if concept has practice problems
    has_practice = ProblemSet.query.filter_by(
        concept_id=concept.id, is_active=True
    ).first() is not None

    # Concept-level resources
    concept_resources = concept.resources.filter_by(is_active=True).order_by(Resource.display_order).all()

    # Update progress for authenticated users
    if current_user.is_authenticated and not show_teaser:
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
        course=course,
        topic=topic,
        concept=concept,
        concept_resources=concept_resources,
        prev_concept=prev_concept,
        next_concept=next_concept,
        has_practice=has_practice,
        show_teaser=show_teaser,
    )


@subjects_bp.route('/<subject_slug>/<course_slug>/<topic_slug>/<concept_slug>/practice/')
def practice_page(subject_slug, course_slug, topic_slug, concept_slug):
    subject = Subject.query.filter_by(slug=subject_slug, is_active=True).first_or_404()
    course = Course.query.filter_by(
        subject_id=subject.id, slug=course_slug, is_active=True
    ).first_or_404()
    topic = Topic.query.filter_by(
        course_id=course.id, slug=topic_slug, is_active=True
    ).first_or_404()

    # Look up concept through TopicConcept
    link = TopicConcept.query.join(Concept).filter(
        TopicConcept.topic_id == topic.id,
        Concept.slug == concept_slug,
        Concept.is_active == True,
    ).first_or_404()
    concept = link.concept

    # Get the first active problem set for this concept
    problem_set = ProblemSet.query.filter_by(
        concept_id=concept.id, is_active=True
    ).order_by(ProblemSet.display_order).first()

    if not problem_set:
        return render_template(
            'study/practice.html',
            subject=subject, course=course, topic=topic, concept=concept,
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
        if p.problem_type == 'code' and p.starter_code:
            pdata['starter_code'] = p.starter_code
        pdata['hint_count'] = p.hints.count()
        pdata['has_solution'] = p.solution is not None
        problems_data.append(pdata)

    import json
    problems_json = json.dumps(problems_data)
    has_code_problems = any(p.problem_type == 'code' for p in problems)

    return render_template(
        'study/practice.html',
        subject=subject,
        course=course,
        topic=topic,
        concept=concept,
        problem_set=problem_set,
        problems_json=problems_json,
        total_problems=len(problems),
        total_available=total_available,
        is_premium=is_premium,
        has_code_problems=has_code_problems,
    )


@subjects_bp.route('/<slug>/courses-json')
def courses_json(slug):
    subject = Subject.query.filter_by(slug=slug, is_active=True).first_or_404()
    courses = Course.query.filter_by(
        subject_id=subject.id, is_active=True
    ).order_by(Course.display_order).all()
    return {
        'courses': [
            {'name': c.name, 'slug': c.slug,
             'url': url_for('subjects.course_detail', subject_slug=slug, course_slug=c.slug)}
            for c in courses
        ]
    }

"""Load qhsJSON content files into the database.

New JSON structure (v3 — 4-level hierarchy):
{
  "subject_slug": "mathematics",
  "course_slug": "ap-calculus-ab",
  "topics": [
    {
      "name": "Limits and Continuity",
      "slug": "limits-and-continuity",
      "description": "...",
      "concepts": [
        { "title": "...", "slug": "...", ... , "problem_sets": [...] }
      ]
    }
  ]
}
"""
import json
import logging
from app.extensions import db
from app.models.content import Subject, Course, Topic, Concept, TopicConcept
from app.models.practice import ProblemSet, Problem, Choice, Hint, StepByStepSolution
from app.utils.sanitize import sanitize_html

logger = logging.getLogger(__name__)


def _delete_concept_problems(concept):
    """Delete all problem sets, problems, choices, hints, and solutions for a concept."""
    for ps in ProblemSet.query.filter_by(concept_id=concept.id).all():
        for problem in Problem.query.filter_by(problem_set_id=ps.id).all():
            Choice.query.filter_by(problem_id=problem.id).delete()
            Hint.query.filter_by(problem_id=problem.id).delete()
            StepByStepSolution.query.filter_by(problem_id=problem.id).delete()
            db.session.delete(problem)
        db.session.delete(ps)
    db.session.flush()


def load_content_json(file_path):
    """Load a qhsJSON file and import its topics/concepts/problems.

    Returns a dict of counts or None if content already loaded.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    subject = Subject.query.filter_by(slug=data['subject_slug']).first()
    if not subject:
        raise ValueError(f"Subject '{data['subject_slug']}' not found")

    course = Course.query.filter_by(subject_id=subject.id, slug=data['course_slug']).first()
    if not course:
        raise ValueError(f"Course '{data['course_slug']}' not found in {subject.name}")

    counts = {'topics': 0, 'concepts': 0, 'problem_sets': 0, 'problems': 0,
              'choices': 0, 'hints': 0, 'solutions': 0}

    for ti, tdata in enumerate(data.get('topics', [])):
        topic_slug = tdata.get('slug', tdata.get('name', f'topic-{ti+1}').lower().replace(' ', '-'))
        topic = Topic.query.filter_by(course_id=course.id, slug=topic_slug).first()
        if not topic:
            topic = Topic(
                course_id=course.id,
                name=tdata.get('name', f'Topic {ti + 1}'),
                slug=topic_slug,
                description=tdata.get('description', ''),
                display_order=tdata.get('display_order', ti),
                is_active=True,
            )
            db.session.add(topic)
            db.session.flush()
            counts['topics'] += 1
        else:
            # Update existing topic fields
            topic.name = tdata.get('name', topic.name)
            topic.description = tdata.get('description', topic.description)
            topic.display_order = tdata.get('display_order', ti)

        for ci, cdata in enumerate(tdata.get('concepts', [])):
            slug = cdata.get('slug', cdata.get('title', f'concept-{ci+1}').lower().replace(' ', '-'))

            concept = Concept.query.filter_by(slug=slug).first()
            if concept:
                # Update existing concept fields
                concept.title = cdata.get('title', concept.title)
                concept.content_html = sanitize_html(cdata.get('content_html', concept.content_html or ''))
                concept.content_raw = cdata.get('content_raw', concept.content_raw or '')
                concept.estimated_minutes = cdata.get('estimated_minutes', concept.estimated_minutes)
                concept.access_tier = cdata.get('access_tier', concept.access_tier)
                concept.subject_area = cdata.get('subject_area', concept.subject_area)
                concept.difficulty = cdata.get('difficulty', concept.difficulty)
                concept.tags = cdata.get('tags', concept.tags)

                # Delete old problem sets and their children, then re-create
                _delete_concept_problems(concept)
            else:
                concept = Concept(
                    title=cdata.get('title', f'Concept {ci + 1}'),
                    slug=slug,
                    content_html=sanitize_html(cdata.get('content_html', '')),
                    content_raw=cdata.get('content_raw', ''),
                    estimated_minutes=cdata.get('estimated_minutes', 5),
                    access_tier=cdata.get('access_tier', 'free'),
                    is_active=True,
                    subject_area=cdata.get('subject_area'),
                    difficulty=cdata.get('difficulty', 'medium'),
                    tags=cdata.get('tags', []),
                )
                db.session.add(concept)
                db.session.flush()
            counts['concepts'] += 1

            # Create problem sets
            for psi, psdata in enumerate(cdata.get('problem_sets', [])):
                ps = ProblemSet(
                    concept_id=concept.id,
                    title=psdata.get('title', f'Problem Set {psi + 1}'),
                    access_tier=psdata.get('access_tier', 'free'),
                    display_order=psdata.get('display_order', psi),
                    is_active=True,
                )
                db.session.add(ps)
                db.session.flush()
                counts['problem_sets'] += 1

                for pi, pdata in enumerate(psdata.get('problems', [])):
                    problem_type = pdata.get('problem_type', 'mcq')
                    if problem_type not in ('mcq', 'ftb', 'frq'):
                        problem_type = 'mcq'
                    problem = Problem(
                        problem_set_id=ps.id,
                        question_html=sanitize_html(pdata.get('question_html', '')),
                        question_raw=pdata.get('question_raw', ''),
                        problem_type=problem_type,
                        correct_answer=pdata.get('correct_answer', ''),
                        difficulty=pdata.get('difficulty', 'medium'),
                        points=pdata.get('points', 1),
                        display_order=pdata.get('display_order', pi),
                    )
                    db.session.add(problem)
                    db.session.flush()
                    counts['problems'] += 1

                    for chi, chdata in enumerate(pdata.get('choices', [])):
                        choice = Choice(
                            problem_id=problem.id,
                            choice_text=chdata.get('text', chdata.get('choice_text', '')),
                            is_correct=chdata.get('is_correct', False),
                            display_order=chi,
                        )
                        db.session.add(choice)
                        counts['choices'] += 1

                    for hi, hdata in enumerate(pdata.get('hints', [])):
                        hint_text = hdata if isinstance(hdata, str) else hdata.get('text', hdata.get('hint_text', ''))
                        cost = 0 if isinstance(hdata, str) else hdata.get('cost_points', 0)
                        hint = Hint(
                            problem_id=problem.id,
                            hint_text=hint_text,
                            display_order=hi,
                            cost_points=cost,
                        )
                        db.session.add(hint)
                        counts['hints'] += 1

                    solution_data = pdata.get('solution_steps', pdata.get('solution'))
                    if solution_data:
                        if isinstance(solution_data, list):
                            steps = []
                            for i, s in enumerate(solution_data):
                                if isinstance(s, str):
                                    steps.append({'step_number': i + 1, 'text_html': s})
                                else:
                                    steps.append({
                                        'step_number': s.get('step_number', i + 1),
                                        'text_html': s.get('text', s.get('text_html', '')),
                                    })
                        else:
                            steps = []
                        if steps:
                            sol = StepByStepSolution(
                                problem_id=problem.id,
                                steps_json=steps,
                                access_tier='premium',
                            )
                            db.session.add(sol)
                            counts['solutions'] += 1

            # Link concept to topic
            existing_link = TopicConcept.query.filter_by(
                topic_id=topic.id, concept_id=concept.id
            ).first()
            if not existing_link:
                display_order = cdata.get('display_order', ci)
                link = TopicConcept(
                    topic_id=topic.id,
                    concept_id=concept.id,
                    display_order=display_order,
                )
                db.session.add(link)

    db.session.commit()
    logger.info('Content loaded from %s: %s topics, %s concepts, %s problems',
                file_path, counts['topics'], counts['concepts'], counts['problems'])
    return counts

"""Load qhsJSON content files into the database, reusing bulk-import logic."""
import json
from app.extensions import db
from app.models.content import Subject, Topic, Concept
from app.models.practice import ProblemSet, Problem, Choice, Hint, StepByStepSolution
from app.utils.sanitize import sanitize_html


def load_content_json(file_path):
    """Load a qhsJSON file and import its concepts/problems into the database.

    Returns a dict of counts or raises on error.
    Skips if concepts already exist for the given topic.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    subject = Subject.query.filter_by(slug=data['subject_slug']).first()
    if not subject:
        raise ValueError(f"Subject '{data['subject_slug']}' not found")

    topic = Topic.query.filter_by(subject_id=subject.id, slug=data['topic_slug']).first()
    if not topic:
        raise ValueError(f"Topic '{data['topic_slug']}' not found in {subject.name}")

    # Skip if topic already has concepts
    existing = Concept.query.filter_by(topic_id=topic.id).count()
    if existing > 0:
        return None  # already loaded

    counts = {'concepts': 0, 'problem_sets': 0, 'problems': 0,
              'choices': 0, 'hints': 0, 'solutions': 0}

    for ci, cdata in enumerate(data.get('concepts', [])):
        concept = Concept(
            topic_id=topic.id,
            title=cdata.get('title', f'Concept {ci + 1}'),
            slug=cdata.get('slug', cdata.get('title', f'concept-{ci+1}').lower().replace(' ', '-')),
            content_html=sanitize_html(cdata.get('content_html', '')),
            content_raw=cdata.get('content_raw', ''),
            estimated_minutes=cdata.get('estimated_minutes', 5),
            access_tier=cdata.get('access_tier', 'free'),
            display_order=cdata.get('display_order', ci),
            is_active=True,
        )
        db.session.add(concept)
        db.session.flush()
        counts['concepts'] += 1

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
                problem = Problem(
                    problem_set_id=ps.id,
                    question_html=sanitize_html(pdata.get('question_html', '')),
                    question_raw=pdata.get('question_raw', ''),
                    problem_type=pdata.get('problem_type', 'mcq'),
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

    db.session.commit()
    return counts

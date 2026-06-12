"""Scan content/*.json seed files and compare against database state."""
import glob
import json
import logging
import os

from app.models.content import Subject, Course, Topic, Concept, TopicConcept
from app.models.practice import ProblemSet, Problem

logger = logging.getLogger(__name__)


def scan_seed_files(content_dir):
    """Scan all .json files in content_dir, parse each, and compare against DB.

    Returns a sorted list of dicts, one per valid qhsJSON seed file.
    """
    results = []
    json_files = sorted(glob.glob(os.path.join(content_dir, '*.json')))

    for filepath in json_files:
        filename = os.path.basename(filepath)

        # Load and validate JSON
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning('Skipping %s: %s', filename, e)
            continue

        subject_slug = data.get('subject_slug')
        course_slug = data.get('course_slug')
        if not subject_slug or not course_slug:
            continue  # Not a qhsJSON content file

        # Look up subject/course in DB
        subject = Subject.query.filter_by(slug=subject_slug).first()
        course = Course.query.filter_by(slug=course_slug).first()

        entry = {
            'filename': filename,
            'filepath': filepath,
            'subject_slug': subject_slug,
            'course_slug': course_slug,
            'subject_name': subject.name if subject else None,
            'course_name': course.name if course else None,
            'course_type': course.course_type if course else data.get('course_type'),
            'file_stats': {'topics': 0, 'concepts': 0, 'problems': 0},
            'db_stats': {'problems': 0},
            'topics': [],
            'error': None,
            'status': 'not_loaded',
        }

        # Walk file structure and compare against DB
        db_available = subject is not None and course is not None
        file_total_problems = 0
        db_total_problems = 0
        all_exist = True
        any_differ = False

        for topic_data in data.get('topics', []):
            topic_entry = {
                'name': topic_data.get('name', '(unnamed)'),
                'slug': topic_data.get('slug', ''),
                'concepts': [],
            }

            for concept_data in topic_data.get('concepts', []):
                # Count problems in file
                file_problems = 0
                for ps in concept_data.get('problem_sets', []):
                    file_problems += len(ps.get('problems', []))

                # Count problems in DB (only if subject/course exist)
                concept_slug = concept_data.get('slug', '')
                db_problems = 0
                exists_in_db = False

                if db_available:
                    db_concept = Concept.query.join(TopicConcept).join(Topic).filter(
                        Concept.slug == concept_slug,
                        Topic.course_id == course.id,
                    ).first()
                    if db_concept:
                        exists_in_db = True
                        db_problems = Problem.query.join(ProblemSet).filter(
                            ProblemSet.concept_id == db_concept.id
                        ).count()

                if not exists_in_db:
                    all_exist = False
                elif file_problems != db_problems:
                    any_differ = True

                file_total_problems += file_problems
                db_total_problems += db_problems
                entry['file_stats']['concepts'] += 1

                topic_entry['concepts'].append({
                    'title': concept_data.get('title', '(unnamed)'),
                    'slug': concept_slug,
                    'file_problems': file_problems,
                    'db_problems': db_problems,
                    'exists_in_db': exists_in_db,
                })

            entry['topics'].append(topic_entry)

        entry['file_stats']['topics'] = len(data.get('topics', []))
        entry['file_stats']['problems'] = file_total_problems
        entry['db_stats']['problems'] = db_total_problems

        # Determine status
        if not db_available:
            entry['status'] = 'not_loaded'
        elif not all_exist and db_total_problems == 0:
            entry['status'] = 'not_loaded'
        elif all_exist and not any_differ:
            entry['status'] = 'in_sync'
        else:
            entry['status'] = 'differs'

        results.append(entry)

    return results

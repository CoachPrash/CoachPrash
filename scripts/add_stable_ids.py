"""Add stable UUID IDs to every ProblemSet and Problem in qhsJSON content files.

Run once to generate permanent IDs. Idempotent — skips objects that already
have an "id" field. These IDs become the database primary keys, so student
progress (AttemptLog) survives reseeds.
"""
import glob
import json
import os
import sys
import uuid


def add_ids_to_file(filepath):
    """Add UUIDs to all ProblemSets and Problems in a single JSON file.

    Returns (ps_added, prob_added) counts.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ps_added = 0
    prob_added = 0

    for topic in data.get('topics', []):
        for concept in topic.get('concepts', []):
            for ps in concept.get('problem_sets', []):
                if 'id' not in ps:
                    # Insert id as first key
                    ps_id = str(uuid.uuid4())
                    # Rebuild dict with id first
                    new_ps = {'id': ps_id}
                    new_ps.update(ps)
                    ps.clear()
                    ps.update(new_ps)
                    ps_added += 1

                for problem in ps.get('problems', []):
                    if 'id' not in problem:
                        prob_id = str(uuid.uuid4())
                        new_prob = {'id': prob_id}
                        new_prob.update(problem)
                        problem.clear()
                        problem.update(new_prob)
                        prob_added += 1

    if ps_added > 0 or prob_added > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')

    return ps_added, prob_added


def main():
    content_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'content')
    files = sorted(glob.glob(os.path.join(content_dir, '*.json')))

    total_ps = 0
    total_prob = 0

    for fp in files:
        fn = os.path.basename(fp)
        if fn == 'qhsjson_schema.json':
            continue

        ps_added, prob_added = add_ids_to_file(fp)
        total_ps += ps_added
        total_prob += prob_added

        if ps_added or prob_added:
            print(f"[UPDATED] {fn}: {ps_added} problem_set IDs, {prob_added} problem IDs added")
        else:
            print(f"[OK] {fn}: all IDs already present")

    print(f"\nTotal: {total_ps} problem_set IDs + {total_prob} problem IDs added")


if __name__ == '__main__':
    main()

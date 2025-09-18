import os
import json
import argparse
from typing import List


def load_json_array(path: str) -> List[str]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        pass
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--method', type=str, required=False)
    parser.add_argument('--input-root', type=str, default='output')
    args = parser.parse_args()

    root = args.input_root
    methods = [args.method] if args.method else [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]

    for m in methods:
        mdir = os.path.join(root, m)
        problems_path = os.path.join(mdir, 'problem_question_ids.json')
        timeouts_path = os.path.join(mdir, 'timeout_question_ids.json')
        problem_ids = load_json_array(problems_path)
        timeout_ids = set(load_json_array(timeouts_path))
        if not problem_ids:
            continue

        # Decide eval dirs
        ex_dir = None
        o3_dir = None
        for d in os.listdir(mdir):
            if not os.path.isdir(os.path.join(mdir, d)):
                continue
            if d.startswith('EX-') and d.endswith('-eval'):
                ex_dir = os.path.join(mdir, d)
            if d.startswith('o3-') and d.endswith('-eval'):
                o3_dir = os.path.join(mdir, d)

        # Write timeout ids
        if timeout_ids:
            with open(timeouts_path, 'w', encoding='utf-8') as f:
                json.dump(sorted(timeout_ids, key=lambda x: (len(x), x)), f, ensure_ascii=False, indent=2)

        # For un-executable problems (problem - timeout), add score 0 rows into both ex and o3 evals
        unexec_ids = [pid for pid in problem_ids if pid not in timeout_ids]
        if not unexec_ids:
            continue

        for target_dir in [ex_dir, o3_dir]:
            if not target_dir:
                continue
            out_file = os.path.join(target_dir, 'eval_results.json')
            if not os.path.exists(out_file):
                # Skip if eval file missing; script does not reconstruct full rows
                continue
            try:
                rows = json.load(open(out_file, 'r', encoding='utf-8'))
            except Exception:
                rows = []
            existing_ids = set(str(r.get('question_id')) for r in rows)
            # We cannot reconstruct full details here; ensure score=0 entries exist for missing ids
            for pid in unexec_ids:
                if pid in existing_ids:
                    continue
                rows.append({
                    "question_id": pid,
                    "question": None,
                    "evidence": None,
                    "gold_sql": None,
                    "predicted_sql": None,
                    "score": 0.0
                })
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()



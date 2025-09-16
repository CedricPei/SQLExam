import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from evaluators.utils import execute_sql, run_with_timeout


def _equal_ex(pred_df: pd.DataFrame, gold_df: pd.DataFrame, rtol: float, atol: float) -> bool:
    if pred_df.shape[1] != gold_df.shape[1]:
        return False

    def norm(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        if isinstance(v, (int, float, np.integer, np.floating)):
            return float(v)
        if isinstance(v, str):
            s = v.strip()
            try:
                return float(s)
            except Exception:
                return s.casefold()
        return v

    f = lambda s: s.map(norm)
    P = pred_df.apply(f, axis=0)
    G = gold_df.apply(f, axis=0)
    cols = list(P.columns)
    P = P.sort_values(by=cols, kind="mergesort").reset_index(drop=True)
    G = G.sort_values(by=cols, kind="mergesort").reset_index(drop=True)

    if P.shape[0] != G.shape[0]:
        return False

    for c in range(P.shape[1]):
        a = P.iloc[:, c].tolist()
        b = G.iloc[:, c].tolist()
        for x, y in zip(a, b):
            if x is None or y is None:
                if not (x is None and y is None):
                    return False
            elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
                if not np.isclose(float(x), float(y), rtol=rtol, atol=atol, equal_nan=False):
                    return False
            elif x != y:
                return False
    return True


def EX(question: dict, pred_sql: str, rtol: float = 1e-5, atol: float = 1e-8) -> bool:
    db_id = question["db_id"]
    gold_sql = question["gold_sql"]

    gold_df = run_with_timeout(execute_sql, db_id, gold_sql, timeout=45)
    pred_df = run_with_timeout(execute_sql, db_id, pred_sql, timeout=45)
    if gold_df is False or pred_df is False:
        return False

    if gold_df.shape == (1, 1) and pred_df.shape == (1, 1):
        return _equal_ex(pred_df, gold_df, rtol, atol)
    return _equal_ex(pred_df, gold_df, rtol, atol)


def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input_path', default=None)
    args = parser.parse_args()

    input_path = args.input_path if args.input_path else os.path.join(base, 'test.json')
    if not os.path.exists(input_path):
        print(f'Input file not found: {input_path}')
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    results = []
    for q in tqdm(questions):
        try:
            pred_sql = q.get('predicted_sql') or ''
            score = 1.0 if EX(q, pred_sql) else 0.0
        except Exception:
            score = 0.0
        results.append({
            "question_id": q.get("question_id"),
            "question": q.get("question"),
            "evidence": q.get("evidence"),
            "gold_sql": q.get("gold_sql"),
            "predicted_sql": pred_sql,
            "label": q.get("label"),
            "score": score,
        })

    out_dir = os.path.join(base, 'output', 'EX')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'eval_results.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()



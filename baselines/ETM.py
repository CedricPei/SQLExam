import sqlite3
from copy import deepcopy as dc
import os, sys, json
import argparse
from tqdm import tqdm
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'ETM.zip'))
from treeMatch import preprocess, parseTree, compareTrees
from ETM_utils.process_sql import get_schema

def ETM(question, pred_sql) -> bool:
    ALLRULES = [100,101,102,103,104,105,106,107,108,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]

    db_id = question["db_id"]
    project_root = os.path.abspath(os.path.join(BASE_DIR, '..'))
    db = os.path.join(project_root, 'dev_databases', db_id, f'{db_id}.sqlite')
    schema = get_schema(db)
    gold = preprocess(question["gold_sql"], schema)
    pred = preprocess(pred_sql, schema)

    conn = sqlite3.connect(db)
    c = conn.cursor()
    bad = False
    try:
        c.execute("EXPLAIN QUERY PLAN " + gold)
        c.execute("EXPLAIN QUERY PLAN " + pred)
    except Exception:
        bad = True

    if not bad:
        treegold = parseTree(gold)
        try:
            treepred = parseTree(pred)
        except Exception:
            treepred = None
        try:
            treecomp = compareTrees(treegold,treepred,dc(schema), db, ALLRULES)
        except Exception:
            treecomp = False
    else:
        treecomp = False

    return True if treecomp else False

def main():
    base = os.path.abspath(os.path.join(BASE_DIR, '..'))

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input_path', default=None)
    args = parser.parse_args()

    path = args.input_path if args.input_path else os.path.join(base, 'test.json')
    if not os.path.exists(path):
        print(f'Input file not found: {path}')
        return
    with open(path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    results = []
    for q in tqdm(questions):
        try:
            pred_sql = q.get('predicted_sql') or ''
            score = 1.0 if ETM(q, pred_sql) else 0.0
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

    out_dir = os.path.join(base, 'output', 'ETM')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'eval_results.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()

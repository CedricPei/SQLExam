import sqlite3
from copy import deepcopy as dc
import os, sys
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE_DIR, 'ETM.zip'))
from treeMatch import preprocess, parseTree, compareTrees
from ETM_utils.process_sql import get_schema

def ETM(question, pred_sql) -> bool:
    ALLRULES = [100,101,102,103,104,105,106,107,108,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]

    db_id = question["db_id"]
    db = f"dev_databases/{db_id}/{db_id}.sqlite"
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

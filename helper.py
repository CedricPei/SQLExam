import json
import os
import sqlite3
import re
import pandas as pd
import numpy as np
from pathlib import Path
from pandas.util import hash_pandas_object
from typing import Dict, List
import multiprocessing as mp
from typing import Callable, Any

def get_ddl(db: str):
    db_path = Path("dev_databases") / db / f"{db}.sqlite"
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name;"
        ).fetchall()
        return "\n\n".join(ddl + ";" for (ddl,) in rows)

def get_schema(db: str) -> Dict[str, List[str]]:
    db_path = Path("dev_databases") / db / f"{db}.sqlite"
    schema = {}
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name;"
        )
        tables = [row[0] for row in cur.fetchall()]
        for table in tables:
            cur.execute(f"PRAGMA table_info('{table}');")
            cols = [row[1] for row in cur.fetchall()]
            schema[table] = cols
    return schema

def extract_json_from_response(response: str) -> str:
    response = response.strip()
    if isinstance(response, dict):
        return response
    
    for pattern in [r"```(?:json|js|javascript|txt|text)?\s*([\s\S]*?)```", r"```(?:json|js|javascript|txt|text)?\s*([\s\S]*)", r'\{[\s\S]*\}']:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            extracted = match.group(1 if '```' in pattern else 0).strip()
            if extracted:
                return extracted
    return response

def execute_sql(db: str | Path, sql: str) -> pd.DataFrame:
    db_path = Path(db) if isinstance(db, Path) else Path("dev_databases") / db / f"{db}.sqlite"
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(sql, conn)  
        return df

def compare_result(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
    if df1.shape != df2.shape:
        return False
    return hash_dataframe(df1) == hash_dataframe(df2)

def hash_dataframe(df: pd.DataFrame) -> int:
    df_str = df.map(str)
    row_hash = None
    for col in df_str.columns:
        h_col = hash_pandas_object(df_str[col], index=False).to_numpy()
        row_hash = h_col if row_hash is None else np.bitwise_xor(row_hash, h_col)
    return int(np.bitwise_xor.reduce(row_hash))

def _worker(q: mp.Queue, func: Callable[..., Any], args: tuple, kwargs: dict):
    try:
        res = func(*args, **kwargs)
        q.put(res)
    except Exception:
        q.put(False)

def run_with_timeout(func: Callable[..., Any], *args, timeout: float = 2.0, **kwargs) -> bool:
    ctx = mp.get_context("spawn")
    q: mp.Queue = ctx.Queue(maxsize=1)
    p = ctx.Process(target=_worker, args=(q, func, args, kwargs), daemon=True)
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return False
    try:
        return q.get_nowait()
    except Exception:
        return False

def append_to_json_file(data, output_file):
    existing_data = json.load(open(output_file, encoding="utf-8")) if os.path.exists(output_file) else []
    existing_data.append(data)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

def write_result_to_file(question, pred_sql, score, prover_result, refuter_result, output_file="output/eval_results.json"):
    result = {
        "question_id": question["question_id"], 
        "question": question["question"], 
        "evidence": question["evidence"],
        "gold_sql": question["gold_sql"],
        "predicted_sql": pred_sql, 
        "ex": question["ex"],
        "score": score,
        "prover_result": prover_result,
        "refuter_result": refuter_result
    }
    append_to_json_file(result, output_file)
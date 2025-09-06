import json
import os
import sqlite3
import re
import pandas as pd
import numpy as np
from pathlib import Path
from pandas.util import hash_pandas_object
from typing import Dict, List, Callable, Any
import multiprocessing as mp

def _get_db_path(db_id: str) -> Path:
    return Path("dev_databases") / db_id / f"{db_id}.sqlite"

def _execute_db_query(db_id: str, query: str, params: tuple = None):
    db_path = _get_db_path(db_id)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        if params:
            return cur.execute(query, params).fetchall()
        else:
            return cur.execute(query).fetchall()

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
    db_path = Path(db) if isinstance(db, Path) else _get_db_path(db)
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(sql, conn)

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

def write_result_to_file(question, pred_sql, score, prover_result, refuter_result, output_dir="output"):
    output_file = os.path.join(output_dir, "eval_results.json")
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

def get_db_info(db_id: str, sql: str | list[str]) -> str:
    all_tables = [row[0] for row in _execute_db_query(db_id, "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")]
    sql_list = [sql] if isinstance(sql, str) else sql
    involved_tables = list(set(t for single_sql in sql_list for t in all_tables if t.upper() in single_sql.upper()))
    
    schema_lines = []
    for table in involved_tables:
        table_info = _execute_db_query(db_id, f"PRAGMA table_info('{table}');")
        fk_info = _execute_db_query(db_id, f"PRAGMA foreign_key_list('{table}');")
        fk_dict = {fk[3]: f"{fk[2]}.{fk[4]}" for fk in fk_info}
        
        col_definitions = []
        for col in table_info:
            col_def = f"{col[1]} {col[2]}"
            if col[5]: col_def += " PRIMARY KEY"
            if col[1] in fk_dict: col_def += f" foreign key({fk_dict[col[1]]})"
            col_definitions.append(col_def)
        schema_lines.append(f"{table} ({', '.join(col_definitions)})\n")
    
    descriptions = []
    desc_file = Path("data/description") / f"{db_id}_schema.json"
    if desc_file.exists():
        with open(desc_file, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        for table in involved_tables:
            if table in schema_data:
                table_desc = f"-- Table: {table}\n"
                for col in schema_data[table]:
                    col_name, col_desc, val_desc = col.get("column_name"), col.get("column_description"), col.get("value_description")
                    if col_desc and val_desc:
                        table_desc += f"  {col_name}: {col_desc}; value_description: {val_desc}\n"
                    elif col_desc:
                        table_desc += f"  {col_name}: {col_desc}\n"
                    elif val_desc:
                        table_desc += f"  {col_name}: {val_desc}\n"
                descriptions.append(table_desc)
    
    result = f"Database: {db_id}\n"
    if schema_lines: result += "Schema:\n" + "\n".join(schema_lines) + "\n\n"
    if descriptions: result += "Descriptions:\n" + "\n".join(descriptions)
    return result
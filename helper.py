import json
import os
import sqlite3
import re
import pandas as pd
import numpy as np
from pathlib import Path
from pandas.util import hash_pandas_object
from typing import Dict, List

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
    match = re.search(r"```(?:json|js|javascript|txt|text)?\s*([\s\S]*?)```", response, re.IGNORECASE)
    extracted = match.group(1).strip() if match else response.strip()
    
    if extracted and not extracted.startswith('['):
        extracted = '[' + extracted
    if extracted and not extracted.endswith(']'):
        extracted = extracted + ']'
    return extracted

def execute_sql(db: str | Path, sql: str) -> pd.DataFrame:
    db_path = Path(db) if isinstance(db, Path) else Path("dev_databases") / db / f"{db}.sqlite"
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(sql, conn)  
        df.columns = range(len(df.columns))
        return df

def execute_and_compare(db: str | Path, gold_sql: str, pred_sql: str) -> bool:
    df1 = execute_sql(db, gold_sql)
    df2 = execute_sql(db, pred_sql)
    if df1.shape != df2.shape:
        return False

    def hash_dataframe(df: pd.DataFrame) -> int:
        df_str = df.map(str)
        row_hash = None
        for col in df_str.columns:
            h_col = hash_pandas_object(df_str[col], index=False).to_numpy()
            row_hash = h_col if row_hash is None else np.bitwise_xor(row_hash, h_col)
        return int(np.bitwise_xor.reduce(row_hash))
    return hash_dataframe(df1) == hash_dataframe(df2)

def write_result_to_file(question, pred_sql, usefulness_score, output_file="usefulness_results.json"):
    result = {"question_id": question["question_id"], "question": question["question"], "predicted_sql": pred_sql, "usefulness": usefulness_score}
    existing_results = json.load(open(output_file, encoding="utf-8")) if os.path.exists(output_file) else []
    existing_results.append(result)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_results, f, ensure_ascii=False, indent=2)
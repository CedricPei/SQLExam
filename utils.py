import os
import sqlite3
import re
import pandas as pd
import numpy as np
from pandas.util import hash_pandas_object
from typing import Dict, List

def get_ddl(db_id: str):
    db_path = os.path.join('dev_databases', db_id, f'{db_id}.sqlite')
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name;"
        ).fetchall()
        return "\n\n".join(ddl + ";" for (ddl,) in rows)

def get_schema(db_id: str) -> Dict[str, List[str]]:
    db_path = os.path.join('dev_databases', db_id, f'{db_id}.sqlite')
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
    if match:
        extracted = match.group(1).strip()
    else:
        extracted = response.strip()    
    
    if extracted and not extracted.startswith('['):
        extracted = '[' + extracted
    if extracted and not extracted.endswith(']'):
        extracted = extracted + ']'
    return extracted

def compare_results(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
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

def execute_sql(db_id: str, sql: str) -> pd.DataFrame:
    db_path = os.path.join('dev_databases', db_id, f'{db_id}.sqlite')    
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(sql, conn)  
        df.columns = range(len(df.columns))
        return df

def execute_and_compare(db_id: str, gold_sql: str, pred_sql: str) -> bool:
    df1 = execute_sql(db_id, gold_sql)
    df2 = execute_sql(db_id, pred_sql)
    return compare_results(df1, df2)
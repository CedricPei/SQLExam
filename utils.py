import os
import sqlite3
import re
import pandas as pd
import numpy as np
from pandas.util import hash_pandas_object

def get_schema_by_db_id(db_id: str):
    db_path = os.path.join('dev_databases', db_id, f'{db_id}.sqlite')
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"No such sqlite database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rows = conn.execute(
        "SELECT sql FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name;"
    ).fetchall()
    conn.close()

    return "\n\n".join(ddl + ";" for (ddl,) in rows)


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
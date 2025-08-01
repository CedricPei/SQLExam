import os
import glob
import sqlite3
import re

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
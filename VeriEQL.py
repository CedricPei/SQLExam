import os, sys, zipfile, shutil, atexit
import sqlite3
import re
from typing import Tuple, Dict, List, Any
import sqlglot
BASE_DIR = os.path.dirname(__file__)
tmp = os.path.join(BASE_DIR, ".verieql_temp")
os.makedirs(tmp, exist_ok=True)
zipfile.ZipFile(os.path.join(BASE_DIR, "verieql.zip")).extractall(tmp)
sys.path.insert(0, os.path.join(tmp, "verieql"))
sys.path.insert(0, tmp)
atexit.register(lambda: shutil.rmtree(tmp, ignore_errors=True))

from verieql.constants import DIALECT
from verieql.environment import Environment

def VeriEQL(db_id, sql1, sql2, **kwargs) -> bool:
    schema, constraints = transpile_schema_to_mysql(db_id)
    sql1 = transpile_query_to_mysql(sql1)
    sql2 = transpile_query_to_mysql(sql2)
    try:
        config = {
            'generate_code': False,  
            'timer': False,  
            'show_counterexample': False,  
            'dialect': DIALECT.MYSQL,  
            **kwargs
        }
        with Environment(**config) as env:
            for table_name, attributes in schema.items():
                env.create_database(
                    attributes=attributes, 
                    bound_size=2,  
                    name=table_name
                )
            if constraints:
                env.add_constraints(constraints)
            env.save_checkpoints()
            result = env.analyze(sql1, sql2)
            return result == True
            
    except Exception as e:
        # print(f"VeriEQL error: {e}")
        return False

def to_mysql_type(sqlite_type: str) -> str:
    t = (sqlite_type or '').strip().upper()
    if re.search(r"INT|INTEGER|TINYINT|SMALLINT|MEDIUMINT|BIGINT", t):
        return "INT"
    if re.search(r"NUMERIC|DECIMAL", t):
        return "DECIMAL(65,30)"
    if re.search(r"REAL|DOUBLE|FLOAT", t):
        return "DOUBLE"
    if re.search(r"CHAR|VARCHAR|CLOB|TEXT", t):
        return "TEXT"
    if re.search(r"BLOB", t):
        return "BLOB"
    if re.search(r"DATETIME|TIMESTAMP", t):
        return "TIMESTAMP"
    if re.search(r"DATE|TIME", t):
        return "DATE"
    return "TEXT"


def transpile_schema_to_mysql(db_id: str) -> Tuple[Dict[str, Dict[str, str]], List[Dict[str, Any]]]:
    db_path = os.path.join('dev_databases', db_id, f'{db_id}.sqlite')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    tables = [row['name'] for row in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )]

    schema = {}
    constraints = []

    for tbl in tables:
        tbl_name = tbl.upper()
        cols = cur.execute(f"PRAGMA table_info('{tbl}');").fetchall()
        schema[tbl_name] = {}
        for c in cols:
            col = c['name'].upper()
            col_type = c['type'] or ''
            schema[tbl_name][col] = to_mysql_type(col_type)

        pk_cols = [c['name'].upper() for c in cols if c['pk']]
        if pk_cols:
            constraints.append({
                'primary': [{'value': f"{tbl_name}__{col}"} for col in pk_cols]
            })

        fks = cur.execute(f"PRAGMA foreign_key_list('{tbl}');").fetchall()
        for fk in fks:
            src = fk['from']
            ref_tbl = fk['table']
            ref_col = fk['to']
            
            if src and ref_tbl:
                src = src.upper()
                ref_tbl = ref_tbl.upper()
                
                if ref_col is None:
                    ref_table_cols = cur.execute(f"PRAGMA table_info('{ref_tbl}');").fetchall()
                    ref_pk_cols = [c['name'].upper() for c in ref_table_cols if c['pk']]
                    if ref_pk_cols:
                        ref_col = ref_pk_cols[0]
                    else:
                        continue
                else:
                    ref_col = ref_col.upper()
                constraints.append({
                    'foreign': [
                        {'value': f"{tbl_name}__{src}"},
                        {'value': f"{ref_tbl}__{ref_col}"}
                    ]
                })
    conn.close()
    return schema, constraints

def transpile_query_to_mysql(sql):
    return sqlglot.transpile(sql, read="sqlite", write="mysql", identify=True, pretty=False)[0] 


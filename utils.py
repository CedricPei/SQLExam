import os
import glob
import sqlite3
import re
import pandas as pd
import numpy as np
from pandas.util import hash_pandas_object
from typing import Any, List, Tuple
from __future__ import annotations
from sqlglot import parse_one, diff, exp
from sqlglot.optimizer import optimize, OPTIMIZER_RULES
from sqlglot.optimizer.qualify import qualify

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

def compare_result_dfs(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
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



def sqlglot_equivalent(gt_sql: str, pred_sql: str, schema: dict[str, list[str]]) -> bool:
    SAFE_RULES = {"qualify", "expand_stars", "normalize", "unqualify_star", "normalize_identifiers"}

    def _canonical(sql: str) -> Tuple[exp.Expression, List[str]]:
        tree = parse_one(sql, read="sqlite")
        tree = qualify(tree, schema=schema, expand_alias_refs=True)
        tree = optimize(tree, schema=schema, rules=[r for r in OPTIMIZER_RULES if r.__name__ in SAFE_RULES])

        order_keys: List[str] = []
        for order in list(tree.find_all(exp.Order)):
            order_keys.extend([e.sql(dialect="sqlite") for e in order.expressions])
            order.parent.set("order", None)

        def _strip_aliases(node: exp.Expression) -> exp.Expression:
            if isinstance(node, exp.Alias):
                return node.this
            if "alias" in node.arg_types:
                node.set("alias", None)
            return node

        tree = tree.transform(_strip_aliases)
        return tree, order_keys

    try:
        ast_gt, order_gt = _canonical(gt_sql)
        ast_pred, order_pred = _canonical(pred_sql)

        if order_gt != order_pred:
            return False

        for edit in diff.diff(ast_gt, ast_pred):
            if not isinstance(edit, (diff.Move, diff.Keep)):
                return False
        return True
    except Exception as exc:
        print(f"sqlglot_equivalent error: {exc}")
        return False
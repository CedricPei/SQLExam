from __future__ import annotations
from ast import Set
import sqlite3, random, pathlib
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import uuid
from helper import execute_and_compare, get_ddl
from faker import Faker

fake = Faker()
def random_value(col_type: str, is_pk: bool = False) -> Any:
    t = col_type.upper()
    if is_pk:
        return None if "INT" in t else uuid.uuid4().hex         
    if "DATETIME" in t:
        return fake.date_time_this_decade().isoformat(sep=" ")
    if "DATE" in t and "TIME" not in t:
        return fake.date()
    if "TIME" in t:
        return fake.time()
    if "BOOL" in t:
        return random.choice([0, 1])
    if any(k in t for k in ("INT", "NUM")):
        return random.randint(0, 1_000_000)
    if any(k in t for k in ("REAL", "FLOA", "DOUB", "DEC")):
        return round(random.uniform(0, 1_000_000), 2)
    return uuid.uuid4().hex

def topological_tables(conn: sqlite3.Connection) -> List[str]:
    edges: List[Tuple[str, str]] = []
    tables = [
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    for child in tables:
        for _, _, parent, *_ in conn.execute(f"PRAGMA foreign_key_list('{child}')"):
            edges.append((child, parent))
    order: List[str] = []
    remaining = set(tables)
    while remaining:
        acyclic = [t for t in remaining if all(e[0] != t for e in edges)]
        if not acyclic:
            order.extend(sorted(remaining))
            break
        order.extend(sorted(acyclic))
        remaining -= set(acyclic)
        edges = [e for e in edges if e[1] not in acyclic]
    return order

def get_unique_cols(cur: sqlite3.Cursor) -> Dict[str, Set[str]]:
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )]
    unique_cols_map: Dict[str, Set[str]] = {}
    for tbl in tables:
        cols = cur.execute(f"PRAGMA table_info('{tbl}')").fetchall()
        pk_cols = {c[1] for c in cols if c[5]}
        uniq = set()
        for _, idx_name, is_unique, *_ in cur.execute(f"PRAGMA index_list('{tbl}')"):
            if is_unique:
                infos = cur.execute(f"PRAGMA index_info('{idx_name}')").fetchall()
                if len(infos) == 1:
                    uniq.add(infos[0][2])
        unique_cols_map[tbl] = pk_cols | uniq
    return unique_cols_map

def make_random_db(ddl: str, dest: pathlib.Path, rows_per_table: int = 20):
    with sqlite3.connect(dest) as conn:
        cur = conn.cursor()
        cur.executescript(ddl)

        unique_cols_map = get_unique_cols(cur)
        unique_vals     = defaultdict(lambda: defaultdict(set))
        pk_vals         = defaultdict(list)
        inserting: Set[str] = set()

        def ensure_parent_key(parent_tbl: str):
            if pk_vals[parent_tbl]:
                return random.choice(pk_vals[parent_tbl])
            if parent_tbl in inserting:
                return None
            inserting.add(parent_tbl)
            insert_single_row(parent_tbl)
            inserting.remove(parent_tbl)
            return pk_vals[parent_tbl][-1]

        def insert_single_row(tbl: str):
            cols      = cur.execute(f"PRAGMA table_info('{tbl}')").fetchall()
            col_names, col_types = zip(*[(c[1], c[2]) for c in cols])
            pk_idx, pk_col = next(((c[0], c[1]) for c in cols if c[5]), (None, None))
            fk_map = {fk[3]: fk for fk in cur.execute(f"PRAGMA foreign_key_list('{tbl}')")}

            ins_sql = 'INSERT INTO "{}" ({}) VALUES ({});'.format(
                tbl,
                ", ".join(f'"{c}"' for c in col_names),
                ", ".join("?" for _ in col_names)
            )

            for attempt in range(5):
                row = []
                for name, ctype in zip(col_names, col_types):
                    if name in fk_map:
                        val = ensure_parent_key(fk_map[name][2])
                    elif name == pk_col:
                        val = random_value(ctype, is_pk=True)
                    else:
                        val = random_value(ctype)
                    if name in unique_cols_map.get(tbl, set()):
                        used = unique_vals[tbl][name]
                        while val in used:
                            val = random_value(ctype)
                        used.add(val)
                    row.append(val)
                try:
                    cur.execute(ins_sql, row)
                    break
                except sqlite3.IntegrityError:
                    if attempt == 4:
                        raise
                    continue

            if pk_idx is not None:
                pk_vals[tbl].append(cur.lastrowid if row[pk_idx] is None else row[pk_idx])

        for tbl in topological_tables(conn):
            for _ in range(rows_per_table):
                insert_single_row(tbl)
        conn.commit()

def RandomDBEval(db_id: str, gold_sql: str, pred_sql: str, n_dbs: int = 50, rows_per_table: int = 20):
    ddl = get_ddl(db_id)
    matches = 0

    base = pathlib.Path(__file__).parent.resolve() / "rand_dbs" / db_id
    base.mkdir(parents=True, exist_ok=True)

    for i in range(n_dbs):
        new_db = base / f"{db_id}_{i}.sqlite"
        if not new_db.exists():
            make_random_db(ddl, new_db, rows_per_table)
        if execute_and_compare(new_db, gold_sql, pred_sql):
            matches += 1
    return round(matches / n_dbs, 2)

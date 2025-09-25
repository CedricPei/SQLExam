#!/usr/bin/env python3

import os
import re
import json
import sqlite3
from pathlib import Path
from typing import Optional

import openai
from tqdm import tqdm
from dotenv import load_dotenv

import sys
BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv()

MODEL = "gpt-5"

def _is_sql_executable(db_file: Path, sql: str) -> bool:
    try:
        with sqlite3.connect(db_file) as conn:
            conn.execute(sql)
        return True
    except Exception:
        return False

def _build_full_schema_context(db_id: str) -> str:
    db = BASE_DIR / "dev_databases" / db_id / f"{db_id}.sqlite"
    if not db.exists():
        return "Schema:\n"
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")]
        schema_lines = []
        for t in tables:
            cols = cur.execute(f"PRAGMA table_info('{t}')").fetchall()
            fks = cur.execute(f"PRAGMA foreign_key_list('{t}')").fetchall()
            fk_dict = {fk[3]: f"{fk[2]}.{fk[4]}" for fk in fks}
            col_defs = []
            for c in cols:
                d = f"{c[1]} {c[2]}"
                if c[5]:
                    d += " PRIMARY KEY"
                if c[1] in fk_dict:
                    d += f" foreign key({fk_dict[c[1]]})"
                col_defs.append(d)
            schema_lines.append(f"{t} ({', '.join(col_defs)})\n")
    return "Schema:\n" + "\n".join(schema_lines)


def _extract_first_sql(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"```sql\s*([\s\S]*?)```", text, re.IGNORECASE)
    if m and m.group(1).strip():
        return _first_statement(m.group(1).strip())
    m = re.search(r"```[\w-]*\s*([\s\S]*?)```", text)
    if m and m.group(1).strip():
        return _first_statement(m.group(1).strip())
    candidates = re.split(r";\s*", text)
    for cand in candidates:
        s = cand.strip()
        if re.match(r"^(WITH|SELECT|INSERT|UPDATE|DELETE)\b", s, re.IGNORECASE):
            return s + ";"
    return None


def _first_statement(sql: str) -> str:
    parts = re.split(r";\s*", sql)
    return (parts[0].strip() + ";") if parts and parts[0].strip() else sql.strip()


def generate_sql(db_id: str, question: str, evidence: str = "", max_attempts: int = 5) -> Optional[str]:

    schema = _build_full_schema_context(db_id)

    db_file = BASE_DIR / "dev_databases" / db_id / f"{db_id}.sqlite"

    system_prompt = """
### ROLE
You translate a natural-language question (plus optional evidence) into ONE correct SQLite query using the given schema.

### OUTPUT
Return EXACTLY ONE executable SQL statement and nothing else (no code fences, comments, or explanations).

### DO THESE STEPS SILENTLY
1) Decide answer shape & grain
- Is the answer a single number, a top-1 entity, or a list?
- What is the base entity? What filters/time windows/metrics/superlatives (max/min/top-N) are required?
2) Map to schema & joins
- Identify necessary tables/columns from the schema only.
- Join via PK/FK or exact same-named keys; avoid cartesian products.
- Default INNER JOIN; use LEFT JOIN only when the question implies including “no/zero” cases.
3) Aggregate correctly (avoid double counting)
- Pre-aggregate at the correct grain in a CTE when a later join would duplicate rows.
- Use GROUP BY for any non-aggregated selected columns.
- Put aggregate filters in HAVING.
- Counting entities → COUNT(DISTINCT <entity_id>); counting rows → COUNT(*).
4) Apply precision rules
- Use table aliases and qualify columns if multiple tables appear; do NOT use SELECT *.
- NULL checks use IS NULL / IS NOT NULL (never = NULL).
- Ratios/percentages use REAL math (e.g., 100.0 * num / NULLIF(den, 0)).
- For numbers stored as TEXT, CAST(x AS REAL) before comparing or dividing.
- Dates stored as text: follow evidence/format, using substr/strftime where appropriate.
- Superlatives/Top-N: ORDER BY the target metric, then stable tie-breakers (e.g., name ASC, id ASC), then LIMIT N.
- Avoid window functions unless clearly necessary; prefer CTE + GROUP BY for compatibility.
5) Sanity check (do not output this)
- Columns/tables exist; joins are correct; DISTINCT vs row-count matches the question intent.
- Aggregates + GROUP BY/HAVING consistent; REAL division ensured; deterministic ORDER BY for top/min/max.
- Projection returns only what the question asks (no extra columns).
    """

    user_prompt = f"""
### Task: Write ONE SQLite query that answers the question using ONLY the schema below.
### Output must be a single SQL statement (CTE allowed). Do not include explanations, comments, or code fences.

### Question:
{question}

### Evidence (may clarify encodings/tie-breaking/date formats and expected answer shape):
{evidence}

### Schema (SQLite):
{schema}
    """

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))

    last_sql: Optional[str] = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = resp.choices[0].message.content
            sql = _extract_first_sql(content)
            last_sql = sql
            if sql and _is_sql_executable(db_file, sql):
                return sql
        except Exception:
            pass

    return last_sql

def main():
    try:
        mini_path = BASE_DIR / "data/mini_dev.json"
        with open(mini_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        # 直接使用每条item中的SQL字段作为gold_sql
        out_dir = BASE_DIR / "data/method_result_mini_dev"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{MODEL}-result.json"

        existing_results = []
        processed_ids = set()
        if out_file.exists():
            try:
                with open(out_file, "r", encoding="utf-8") as f:
                    existing_results = json.load(f)
                for r in existing_results:
                    qid = r.get("question_id")
                    if qid is not None:
                        processed_ids.add(qid)
            except Exception:
                pass

        results = list(existing_results)
        non_exec_count = 0

        for item in tqdm(items, desc="NL2SQL mini_dev"):
            db_id = item.get("db_id", "")
            question = item.get("question", "")
            evidence = item.get("evidence", "")
            qid = item.get("question_id")
            gold_sql = item.get("SQL", "")
            if qid in processed_ids:
                continue
            pred = generate_sql(db_id, question, evidence, 5)
            db_file = BASE_DIR / "dev_databases" / db_id / f"{db_id}.sqlite"
            if not pred or not _is_sql_executable(db_file, pred):
                non_exec_count += 1
            results.append({
                "question_id": qid,
                "db_id": db_id,
                "question": question,
                "predicted_sql": pred or "",
                "gold_sql": gold_sql,
                "evidence": evidence,
                "difficulty": item.get("difficulty", "")
            })
            try:
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        try:
            print(f"non_executable_count: {non_exec_count}")
        except Exception:
            pass
    except Exception:
        pass

if __name__ == "__main__":
    main()



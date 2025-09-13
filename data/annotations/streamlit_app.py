import streamlit as st
import pandas as pd
import sqlite3, os, time, re, io, json, sys, argparse
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
import sqlparse

st.set_page_config(page_title="NL2SQL Annotator", layout="wide")

# --------------------------- Utilities ---------------------------

SQL_READONLY_PREFIXES = ("select", "with", "explain")

def _fallback_pretty_sql(sql: str) -> str:
    s = sql.strip()
    s = re.sub(r"\s+(FROM|WHERE|GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|UNION|EXCEPT|INTERSECT)(\b)", r"\n\1\2", s, flags=re.IGNORECASE)
    keywords = ["select", "from", "where", "group by", "order by", "having", "limit", "join", "left join", "right join", "inner join", "union", "except", "intersect", "on", "and", "or"]
    for kw in sorted(keywords, key=len, reverse=True):
        s = re.sub(rf"\b{re.escape(kw)}\b", kw.upper(), s, flags=re.IGNORECASE)
    return s

def pretty_sql(sql: str) -> str:
    if not sql:
        return ""
    if sqlparse is None:
        return _fallback_pretty_sql(sql)
    try:
        return sqlparse.format(sql, reindent=True, keyword_case="upper", indent_width=2)
    except Exception:
        return _fallback_pretty_sql(sql)

def is_safe_select(sql: str) -> bool:
    s = sql.strip().strip(";")
    lowered = s.lower()
    if lowered.count(";") > 0:
        return False
    if not lowered.startswith(SQL_READONLY_PREFIXES):
        return False
    banned = ["insert", "update", "delete", "drop", "alter", "create", "attach", "reindex", "vacuum", "pragma", "replace", "truncate"]
    for w in banned:
        if re.search(rf"\b{re.escape(w)}\b", lowered):
            return False
    return True

def add_limit(sql: str, max_rows: int = 200) -> str:
    body = sql.strip().rstrip(";")
    lowered = body.lower()
    if " limit " in lowered or lowered.endswith(" limit") or lowered.endswith(" limit("):
        return body
    if lowered.startswith("explain"):
        return body
    return body + f" LIMIT {max_rows}"

def connect_ro(db_path: str, timeout_seconds: float = 1.5, max_ops: int = 1_000_000):
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False, timeout=timeout_seconds)
    try:
        conn.execute("PRAGMA query_only=ON;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        pass
    op_counter = {"count": 0}
    def progress_handler():
        op_counter["count"] += 1
        if op_counter["count"] > max_ops:
            return 1
        return 0
    conn.set_progress_handler(progress_handler, 1000)
    return conn

def run_sql(db_path: str, sql: str, limit_rows: int = 200) -> Tuple[Optional[pd.DataFrame], Optional[str], float]:
    if not is_safe_select(sql):
        return None, "Unsafe or non-readonly SQL blocked.", 0.0
    q = add_limit(sql, limit_rows)
    t0 = time.time()
    try:
        with connect_ro(db_path) as conn:
            df = pd.read_sql_query(q, conn)
        dt = time.time() - t0
        return df, None, dt
    except Exception as e:
        dt = time.time() - t0
        return None, f"{type(e).__name__}: {e}", dt

def get_schema_ddl(db_path: str) -> str:
    try:
        with connect_ro(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT type, name, sql FROM sqlite_master WHERE type IN ('table','view','index','trigger') AND name NOT LIKE 'sqlite_%' ORDER BY type, name;")
            rows = cur.fetchall()
            if not rows:
                return "-- No user tables/views found"
            ddls = []
            for t, n, s in rows:
                if not s:
                    continue
                ddls.append(s.strip().rstrip(";") + ";")
            return "\n\n".join(ddls)
    except Exception as e:
        return f"-- schema error: {e}"


 



def df_equal(a: Optional[pd.DataFrame], b: Optional[pd.DataFrame]) -> Optional[bool]:
    if a is None or b is None:
        return None
    try:
        if a.shape[1] != b.shape[1] or len(a) != len(b):
            return False
        def row_signature(values: List[Any]) -> str:
            out = []
            for v in values:
                try:
                    if pd.isna(v):
                        out.append(None)
                    else:
                        out.append(v)
                except Exception:
                    out.append(v)
            return json.dumps(out, ensure_ascii=False, default=str)
        for i in range(len(a)):
            sig_a = row_signature(a.iloc[i].tolist())
            sig_b = row_signature(b.iloc[i].tolist())
            if sig_a != sig_b:
                return False
        return True
    except Exception:
        return None

def load_items_from_file(path: str) -> List[Dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    if not isinstance(items, list):
        raise ValueError("JSON must be a list or an object with key 'items'.")
    norm = []
    for row in items:
        if "question_id" not in row:
            raise ValueError("Each item must contain 'question_id'.")
        if "db_id" not in row:
            raise ValueError("Each item must contain 'db_id'.")
        norm.append({
            "question_id": row["question_id"],
            "db_id": row["db_id"],
            "question": row.get("question", ""),
            "evidence": row.get("evidence", ""),
            "predicted_sql": row.get("predicted_sql", row.get("pred_sql", "")),
            "gold_sql": row.get("gold_sql", ""),
        })
    return norm

def to_jsonl_str(records: List[Dict[str, Any]]) -> str:
    out = io.StringIO()
    for r in records:
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out.getvalue()

# --------------------------- Sidebar ---------------------------

# Sidebar removed; auto_compare disabled
auto_compare = False

# --------------------------- CLI args ---------------------------
if "cli_parsed" not in st.session_state:
    argv = sys.argv[1:]
    data_path = None
    ann_path = None
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "d" and i + 1 < len(argv):
            data_path = argv[i + 1]
            i += 2
            continue
        if tok == "a" and i + 1 < len(argv):
            ann_path = argv[i + 1]
            i += 2
            continue
        i += 1
    st.session_state["cli_data"] = data_path
    st.session_state["cli_ann"] = ann_path
    st.session_state["cli_parsed"] = True
cli_data = st.session_state.get("cli_data")
cli_ann = st.session_state.get("cli_ann")

# --------------------------- Load Items ---------------------------

try:
    if cli_data:
        source_path = cli_data
    elif cli_ann:
        source_path = cli_ann
    else:
        st.error("Please provide at least one argument using tokens 'd' and/or 'a'.\nUsage: streamlit run streamlit_app.py d <data.json> a <annotations.json>\nOr: streamlit run streamlit_app.py a <annotations.json>")
        st.stop()
    items = load_items_from_file(source_path)
except Exception as e:
    st.error(f"Failed to load json: {e}")
    st.stop()

N = len(items)
if N == 0:
    st.warning("No items loaded.")
    st.stop()

if "idx" not in st.session_state:
    st.session_state["idx"] = 0
if "boot_index_set" not in st.session_state:
    st.session_state["boot_index_set"] = False

def _load_existing_labels() -> Dict[str, Any]:
    try:
        p = Path(cli_ann if cli_ann else "annotations.json")
        if not p.exists():
            return {}
        records = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            return {}
        out: Dict[str, Any] = {}
        for r in records:
            qid = r.get("question_id")
            if qid is not None:
                out[str(qid)] = r  # 统一用 str 作为 key
        return out
    except Exception:
        return {}

if "labels" not in st.session_state:
    st.session_state["labels"] = _load_existing_labels()

def _jump_to_first_unlabeled():
    labels = st.session_state["labels"]
    first_unlabeled_idx = None
    for i, it in enumerate(items):
        if str(it["question_id"]) not in labels:
            first_unlabeled_idx = i
            break
    st.session_state["idx"] = first_unlabeled_idx if first_unlabeled_idx is not None else 0

if not st.session_state["boot_index_set"]:
    _jump_to_first_unlabeled()
    st.session_state["boot_index_set"] = True

if "prev_idx" not in st.session_state:
    st.session_state["prev_idx"] = None

if "started_at" not in st.session_state:
    st.session_state["started_at"] = time.time()

# --------------------------- Header ---------------------------

st.caption(f"Progress: {len(st.session_state['labels'])} / {N}")
st.progress(len(st.session_state["labels"]) / max(N, 1))

# --------------------------- Item Controls (single row) ---------------------------

nav_cols = st.columns([1,1,1,1,3])
with nav_cols[0]:
    if st.button("⏮️ First"):
        st.session_state["idx"] = 0
with nav_cols[1]:
    if st.button("◀️ Prev"):
        st.session_state["idx"] = max(0, st.session_state["idx"] - 1)
with nav_cols[2]:
    if st.button("Next ▶️"):
        st.session_state["idx"] = min(N - 1, st.session_state["idx"] + 1)
with nav_cols[3]:
    if st.button("Last ⏭️"):
        st.session_state["idx"] = N - 1
with nav_cols[4]:
    st.write(f"Index: {st.session_state['idx'] + 1} / {N}")

# --------------------------- Item Panel (single column) ---------------------------

item = items[st.session_state["idx"]]

def _sync_ui_from_label(rec: Optional[Dict[str, Any]]):
    if rec:
        st.session_state["last_clicked"] = "yes" if rec.get("label") else "no"
        st.session_state["reason_text"] = rec.get("reason", "")
    else:
        st.session_state["last_clicked"] = None
        st.session_state["reason_text"] = ""

if st.session_state["prev_idx"] != st.session_state["idx"]:
    existing = st.session_state["labels"].get(str(item["question_id"]))
    _sync_ui_from_label(existing)
    st.session_state["prev_idx"] = st.session_state["idx"]

st.markdown(f"<div style='font-size:1.1rem; color:#666'>DB: `{item['db_id']}`</div>", unsafe_allow_html=True)

_root = Path(__file__).resolve().parents[2]
_db_path = str(_root / "dev_databases" / item["db_id"] / f"{item['db_id']}.sqlite")
if os.path.exists(_db_path):
    def _get_db_description(db_id: str) -> str:
        desc_path = _root / "data" / "description" / f"{db_id}_schema.json"
        if not desc_path.exists():
            return "-- No description found"
        try:
            data = json.loads(desc_path.read_text(encoding="utf-8"))
            parts = []
            for table, cols in data.items():
                parts.append(f"-- Table: {table}")
                for col in cols:
                    name = col.get("column_name", "")
                    cdesc = col.get("column_description")
                    vdesc = col.get("value_description")
                    line = f"  {name}: "
                    details = []
                    if cdesc:
                        details.append(str(cdesc))
                    if vdesc:
                        details.append(f"value_description: {vdesc}")
                    line += "; ".join(details) if details else "(no description)"
                    parts.append(line)
            return "\n".join(parts) if parts else "-- No description content"
        except Exception as e:
            return f"-- description error: {e}"
    with st.expander("📚 Schema", expanded=False):
        ddl = get_schema_ddl(_db_path)
        st.code(ddl, language="sql")
    
    with st.expander("📖 Description", expanded=False):
        desc_text = _get_db_description(item["db_id"])
        st.code(desc_text, language="text")
else:
    st.error(f"DB file not found at: {_db_path}")

# Question (title and content without extra blank line)
st.markdown(
    f"""
    <div style='margin:0;'>
      <div style='font-weight:600; margin:0;'>Question:</div>
      <div style='font-size:1.1rem; margin:0;'>{item['question']}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Evidence (add a blank line before the title)
if item.get('evidence'):
    st.markdown(
        f"""
        <div style='margin-top:0.6rem;'>
          <div style='font-weight:600; margin:0;'>Evidence:</div>
          <div style='font-size:1.1rem; margin:0;'>{item.get('evidence','')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# add extra space between evidence and SQL section
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# Pred/Gold SQL display in two columns with pretty formatting
sql_cols = st.columns(2)
with sql_cols[0]:
    st.markdown("**Predicted SQL**")
    st.code(pretty_sql(item["predicted_sql"]) or "(empty)", language="sql")
with sql_cols[1]:
    st.markdown("**Gold SQL**")
    st.code(pretty_sql(item["gold_sql"]) or "(empty)", language="sql")

# --------------------------- Results (aligned with the same two-column layout) ---------------------------
res_cols = st.columns(2)
pred_df = gold_df = None
pred_err = gold_err = None
pred_time = gold_time = 0.0

if os.path.exists(_db_path):
    if item["predicted_sql"]:
        pred_df, pred_err, pred_time = run_sql(_db_path, item["predicted_sql"])
    if item["gold_sql"]:
        gold_df, gold_err, gold_time = run_sql(_db_path, item["gold_sql"])

with res_cols[0]:
    st.markdown("**Predicted result**")
    if pred_err:
        st.error(f"{pred_err}")
    elif pred_df is not None:
        st.caption(f"Rows: {len(pred_df)} • {pred_time*1000:.0f} ms")
        st.dataframe(pred_df, use_container_width=True, hide_index=True)
    else:
        st.info("No predicted result (error or empty).")

with res_cols[1]:
    st.markdown("**Gold result**")
    if gold_err:
        st.error(f"{gold_err}")
    elif gold_df is not None:
        st.caption(f"Rows: {len(gold_df)} • {gold_time*1000:.0f} ms")
        st.dataframe(gold_df, use_container_width=True, hide_index=True)
    else:
        st.info("No gold result (error or empty).")

# EX line (1 if equal, 0 otherwise)
eq_val = None
try:
    eq_tmp = df_equal(pred_df, gold_df)
    if eq_tmp is True:
        eq_val = 1
    elif eq_tmp is False:
        eq_val = 0
except Exception:
    eq_val = None
st.markdown(f"EX: **{eq_val if eq_val is not None else 'N/A'}**")

# --------------------------- Label Box (single row buttons) ---------------------------

st.divider()
st.subheader("Your judgment")

if "last_clicked" not in st.session_state:
    st.session_state["last_clicked"] = None
if "reason_text" not in st.session_state:
    st.session_state["reason_text"] = ""

# Helper to save and update highlight
def _save_label(is_yes: bool) -> None:
    rec = {
        "question_id": item["question_id"],
        "db_id": item["db_id"],
        "question": item["question"],
        "predicted_sql": item["predicted_sql"],
        "gold_sql": item["gold_sql"],
        "label": bool(is_yes),
        "reason": (st.session_state.get("reason_text") or "").strip(),
    }
    st.session_state["labels"][str(item["question_id"])] = rec
    try:
        records = list(st.session_state["labels"].values())
        Path(cli_ann if cli_ann else "annotations.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def _set_label_and_save(is_yes: bool) -> None:
    st.session_state["last_clicked"] = "yes" if is_yes else "no"
    _save_label(is_yes)

def _save_and_next() -> None:
    last = st.session_state.get("last_clicked")
    if last in ("yes", "no"):
        is_yes = (last == "yes")
        # if NO, require reason
        if (not is_yes) and len((st.session_state.get("reason_text") or "").strip()) == 0:
            return
        _save_label(is_yes)
    st.session_state["idx"] = min(N - 1, st.session_state["idx"] + 1)

# Read current reason value (even if textarea appears below)
_current_reason = (st.session_state.get("reason_text") or "").strip()

yn_cols = st.columns([1,1,6])
with yn_cols[0]:
    st.button(
        "✅ YES",
        type=("primary" if st.session_state.get("last_clicked") == "yes" else "secondary"),
        key="btn_yes",
        on_click=_set_label_and_save,
        args=(True,),
    )
with yn_cols[1]:
    st.button(
        "❌ NO",
        type=("primary" if st.session_state.get("last_clicked") == "no" else "secondary"),
        key="btn_no",
        disabled=(len(_current_reason) == 0 and st.session_state.get("last_clicked") != "no"),
        on_click=_set_label_and_save,
        args=(False,),
    )
# Note textarea below the buttons, bound to session state
reason = st.text_area(
    "Note (required if NO)",
    key="reason_text",
    placeholder="Why is it wrong? (aggregation, filter, etc.)",
)

# Save/Next and Skip in the same row
nav2 = st.columns([1,1,6])
# compute disabled state: need a label; if NO, need reason
_disable_save = (
    st.session_state.get("last_clicked") not in ("yes", "no")
) or (
    st.session_state.get("last_clicked") == "no" and len((st.session_state.get("reason_text") or "").strip()) == 0
)
with nav2[0]:
    st.button("⏭️ Save & Next", on_click=_save_and_next, key="btn_save_next", disabled=_disable_save)
with nav2[1]:
    st.button("⏸️ Skip", on_click=lambda: st.session_state.update({"idx": min(N - 1, st.session_state["idx"] + 1)}), key="btn_skip")

current_label = st.session_state["labels"].get(str(item["question_id"]))
if current_label:
    if current_label["label"]:
        st.success("Labeled YES")
    else:
        st.error(f"Labeled NO — {current_label.get('reason','')}")

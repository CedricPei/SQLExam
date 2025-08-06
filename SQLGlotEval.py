import re
from typing import Tuple, List
from sqlglot import parse_one, exp, diff
from sqlglot.optimizer.optimizer import optimize, RULES
from sqlglot.optimizer.qualify import qualify
from sqlglot.schema import ensure_schema
from sqlglot.diff import Move, Keep, Update
from helper import get_schema

_SAFE_RULES = {
    "qualify", "expand_stars", "normalize", "unqualify_star",
    "normalize_identifiers", "pushdown_projections", "pushdown_predicates",
    "optimize_joins", "eliminate_subqueries", "merge_subqueries",
    "eliminate_joins", "eliminate_ctes", "canonicalize", "simplify",
    "unnest_subqueries", "expand_windows",
}

def SQLGlotEval(db_id: str, gt_sql: str, pred_sql: str) -> bool:
    schema = get_schema(db_id)
    schema_obj = ensure_schema({t: {c: None for c in cols} for t, cols in schema.items()})
    rules = [r for r in RULES if r.__name__ in _SAFE_RULES]
    try:
        gt_tree, gt_order = _canonical(gt_sql, schema_obj, rules)
        pr_tree, pr_order = _canonical(pred_sql, schema_obj, rules)
        if gt_order != pr_order:
            return False
        edits = list(diff(gt_tree, pr_tree))
        return all(isinstance(e, (Move, Keep, Update)) for e in edits)
    except Exception as e:
        print(f"Error in SQLGlotEval: {e}")
        return False

def _canonical(sql: str, schema_obj, rules) -> Tuple[exp.Expression, List[str]]:
    tree = parse_one(sql, read="sqlite")
    try:
        qualify(tree, schema=schema_obj, expand_alias_refs=True)
    except:
        tree = parse_one(re.sub(r'`([^`]+)`', r'\1', sql), read="sqlite")
        tree = qualify(tree, schema=schema_obj, expand_alias_refs=True)
    tree = optimize(tree, schema=schema_obj, rules=rules)
    tree = _normalize_count_functions(tree)
    tree = _normalize_group_by_distinct(tree)
    order_keys = _extract_and_remove_order_by(tree)
    tree = _normalize_join_order(tree)
    tree = _remove_aliases_and_qualifiers(tree)
    return tree, order_keys

def _normalize_count_functions(tree: exp.Expression):
    for count_func in tree.find_all(exp.Count):
        literal_arg = None
        if isinstance(count_func.this, exp.Literal):
            literal_arg = count_func.this
        elif count_func.expressions and isinstance(count_func.expressions[0], exp.Literal):
            literal_arg = count_func.expressions[0]
        if literal_arg and literal_arg.is_int and literal_arg.this == "1":
            count_func.set("this", exp.Star())
            count_func.set("expressions", None)
        elif count_func.expressions and isinstance(count_func.expressions[0], exp.Star):
            star = count_func.expressions[0]
            count_func.set("this", star)
            count_func.set("expressions", None)
    return tree

def _normalize_group_by_distinct(tree: exp.Expression):
    if not tree.args.get("group") or any(tree.find_all(exp.AggFunc)):
        return tree
    select_names = {col.alias_or_name for col in tree.selects}
    group_names = {col.alias_or_name for col in tree.args["group"].expressions}
    if select_names == group_names:
        tree.set("group", None)
        tree.set("distinct", exp.Distinct())
    return tree

def _extract_and_remove_order_by(tree: exp.Expression) -> List[str]:
    order_keys = []
    for order in list(tree.find_all(exp.Order)):
        order_keys.extend(expr.sql(dialect="sqlite") for expr in order.expressions)
        order.parent.set("order", None)
    return order_keys

def _remove_aliases_and_qualifiers(tree: exp.Expression):
    def _strip_aliases(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Alias):
            return node.this
        if "alias" in node.arg_types:
            node.set("alias", None)
        return node
    tree = tree.transform(_strip_aliases)

    def _drop_table_alias(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.TableAlias):
            return None
        return node
    tree = tree.transform(_drop_table_alias)
    return tree

def _get_table_name(table: exp.Table) -> str:
    if isinstance(table.this, exp.Identifier):
        return table.this.this.lower()
    return table.sql(dialect="sqlite").lower()

def _normalize_join_order(tree: exp.Expression):
    from_expr = tree.args.get("from")
    joins = tree.args.get("joins") or []
    if not (from_expr and len(joins) == 1 and isinstance(joins[0], exp.Join)):
        return tree
    join_node = joins[0]
    kind = (join_node.args.get("kind") or join_node.kind or "INNER").upper()
    if kind not in ("JOIN", "INNER"):
        return tree
    cond = join_node.args.get("on")
    if not isinstance(cond, exp.EQ):
        return tree
    tables_in_cond = {c.table.lower() for c in cond.find_all(exp.Column) if c.table}
    if len(tables_in_cond) != 2:
        return tree
    left_tbl = from_expr.this
    right_tbl = join_node.this
    if _get_table_name(left_tbl) > _get_table_name(right_tbl):
        from_expr.set("this", right_tbl)
        join_node.set("this", left_tbl)
    return tree
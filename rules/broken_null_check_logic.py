# rule: A null check that is logically broken (uses && where \
# (authored by RuleSmith from the description above)

# rule: A null check that is logically broken (uses && where || is needed, or || where && is needed) so the guard fails to protect a dereference of the same reference in the other operand.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "broken-null-check-logic"


def _unwrap(n):
    while n is not None and n.type == "parenthesized_expression":
        inner = None
        for c in n.named_children:
            inner = c
            break
        if inner is None:
            break
        n = inner
    return n


def _is_null(node, src):
    return node is not None and (
        node.type == "null_literal" or node_text(node, src) == "null"
    )


def _null_check(node, src):
    """If `node` is `ident == null` / `ident != null`, return (name, op) else None."""
    node = _unwrap(node)
    if node is None or node.type != "binary_expression":
        return None
    opn = node.child_by_field_name("operator")
    if opn is None:
        return None
    op = node_text(opn, src)
    if op not in ("==", "!="):
        return None
    left = _unwrap(node.child_by_field_name("left"))
    right = _unwrap(node.child_by_field_name("right"))
    if left is not None and left.type == "identifier" and _is_null(right, src):
        return (node_text(left, src), op)
    if right is not None and right.type == "identifier" and _is_null(left, src):
        return (node_text(right, src), op)
    return None


def _derefs(node, name, src):
    """True if `node` dereferences variable `name` via method call or field access."""
    if node is None:
        return False
    for mi in find(node, "method_invocation"):
        obj = _unwrap(mi.child_by_field_name("object"))
        if obj is not None and obj.type == "identifier" and node_text(obj, src) == name:
            return True
    for fa in find(node, "field_access"):
        obj = _unwrap(fa.child_by_field_name("object"))
        if obj is not None and obj.type == "identifier" and node_text(obj, src) == name:
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    out = []
    for be in find(tree.root_node, "binary_expression"):
        opn = be.child_by_field_name("operator")
        if opn is None:
            continue
        op = node_text(opn, sb)
        if op not in ("&&", "||"):
            continue
        left = be.child_by_field_name("left")
        right = be.child_by_field_name("right")
        for check, deref in ((left, right), (right, left)):
            nc = _null_check(check, sb)
            if nc is None:
                continue
            name, pol = nc
            if not _derefs(deref, name, sb):
                continue
            # != null guards with && (short-circuit skips deref when null);
            # == null guards with || (short-circuit skips deref when null).
            broken = (pol == "!=" and op == "||") or (pol == "==" and op == "&&")
            if not broken:
                continue
            line, col, _, _ = span(be)
            want = "&&" if pol == "!=" else "||"
            out.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"Broken null check: '{name} {pol} null {op} {name}.…' uses '{op}'; "
                    f"short-circuit still dereferences '{name}' when it is null.",
                    "note": node_text(be, sb),
                    "help": f"Use '{want}' so the null check guards the dereference of '{name}'.",
                }
            )
            break
    return out

# rule: Flag explicit boxing via new Integer/Long/Double in arithmetic or comparison contexts that forces allocation; use valueOf or primitives.
# (authored by RuleSmith from the description above)

# rule: Flag explicit boxing via new Integer/Long/Double in arithmetic or comparison contexts that forces allocation; use valueOf or primitives.
"""Flag new Integer/Long/Double boxing used in arithmetic or comparison contexts."""

from rulesmith.parse import parse, find, span, node_text

RULE = "unnecessary-boxing-allocation"

_BOX_TYPES = {"Integer", "Long", "Double", "Float", "Short", "Byte"}
_ARITH = {"+", "-", "*", "/", "%"}
_COMPARE = {"<", ">", "<=", ">=", "==", "!="}
_OPS = _ARITH | _COMPARE


def _enclosing_binary(node):
    # climb through paren/unary wrappers to find a binary_expression this node is an operand of
    cur = node
    parent = cur.parent
    while parent is not None and parent.type in (
        "parenthesized_expression",
        "unary_expression",
    ):
        cur = parent
        parent = cur.parent
    if parent is not None and parent.type == "binary_expression":
        return parent
    return None


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for oce in find(tree.root_node, "object_creation_expression"):
        tnode = oce.child_by_field_name("type")
        if tnode is None:
            continue
        tname = node_text(tnode, src_b)
        if tname not in _BOX_TYPES:
            continue
        binexpr = _enclosing_binary(oce)
        if binexpr is None:
            continue
        op_node = binexpr.child_by_field_name("operator")
        if op_node is None:
            continue
        op = node_text(op_node, src_b)
        if op not in _OPS:
            continue
        line, col, _, _ = span(oce)
        kind = "arithmetic" if op in _ARITH else "comparison"
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"new {tname}(...) forces an allocation in a {kind} context ('{op}')",
                "note": f"object_creation_expression of {tname} is an operand of binary '{op}'",
                "help": f"use {tname}.valueOf(...) or a primitive instead of new {tname}(...)",
            }
        )
    return findings

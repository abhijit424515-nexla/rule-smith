# rule: A binary operator (==, !=, &&, \
# (authored by RuleSmith from the description above)

# rule: A binary operator (==, !=, &&, ||, <, <=, >, >=, -, /, %, &, |, ^) with identical left and right operands, which is almost always a copy-paste bug or redundant logic.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "identical-binary-operands"

# Operators where `x OP x` is redundant or a bug. `+`, `*`, `<<`, `>>` excluded:
# doubling/squaring/shifting by self are legitimate.
SUSPECT_OPS = {
    "==",
    "!=",
    "&&",
    "||",
    "<",
    "<=",
    ">",
    ">=",
    "-",
    "/",
    "%",
    "&",
    "|",
    "^",
}


def _norm(node, src):
    """Normalized operand text: unwrap parens, strip whitespace."""
    while node is not None and node.type == "parenthesized_expression":
        inner = next((c for c in node.named_children), None)
        if inner is None:
            break
        node = inner
    if node is None:
        return None
    return "".join(node_text(node, src).split())


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    out = []
    for be in find(tree.root_node, "binary_expression"):
        opn = be.child_by_field_name("operator")
        if opn is None:
            continue
        op = node_text(opn, sb)
        if op not in SUSPECT_OPS:
            continue
        left = be.child_by_field_name("left")
        right = be.child_by_field_name("right")
        ln, rn = _norm(left, sb), _norm(right, sb)
        if ln is None or rn is None or ln != rn:
            continue
        # `x != x` / `x == x` on a float/double is an intentional NaN check; we
        # can't see types here, so we keep flagging it but the message hints at it.
        line, col, _, _ = span(be)
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Both operands of '{op}' are identical ('{ln}'); "
                f"this is redundant or a copy-paste bug.",
                "note": node_text(be, sb),
                "help": f"Replace one operand or remove the comparison; '{ln} {op} {ln}' "
                f"has a constant result (NaN checks excepted).",
            }
        )
    return out

# rule: A value that cannot be null (this, a new expression, a primitive, or a known non-null reference) must not be compared against null.
# (authored by RuleSmith from the description above)

# rule: A value that cannot be null (this, a new expression, a primitive, or a known non-null reference) must not be compared against null.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "compare-nonnull-to-null"

# Literal / construction node types that can never evaluate to null.
_NONNULL = {
    "this",
    "object_creation_expression",
    "array_creation_expression",
    "string_literal",
    "character_literal",
    "decimal_integer_literal",
    "hex_integer_literal",
    "octal_integer_literal",
    "binary_integer_literal",
    "decimal_floating_point_literal",
    "hex_floating_point_literal",
    "true",
    "false",
}


def _unwrap(node):
    while node is not None and node.type == "parenthesized_expression":
        # parenthesized_expression wraps a single child expression
        inner = [c for c in node.children if c.is_named]
        node = inner[0] if inner else None
    return node


def _is_null(node, src):
    return node is not None and (
        node.type == "null_literal" or node_text(node, src) == "null"
    )


def _label(node, src):
    if node.type == "this":
        return "this"
    if node.type in ("object_creation_expression", "array_creation_expression"):
        return "a new expression"
    return "a non-null value"


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    out = []
    for be in find(tree.root_node, "binary_expression"):
        op = be.child_by_field_name("operator")
        if op is None or node_text(op, sb) not in ("==", "!="):
            continue
        left = _unwrap(be.child_by_field_name("left"))
        right = _unwrap(be.child_by_field_name("right"))
        if left is None or right is None:
            continue
        # exactly one side must be `null`, the other a provably non-null value
        if _is_null(left, sb) and not _is_null(right, sb):
            nn = right
        elif _is_null(right, sb) and not _is_null(left, sb):
            nn = left
        else:
            continue
        if nn.type not in _NONNULL:
            continue
        line, col, _, _ = span(nn)
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": _label(nn, sb)
                + " can never be null; comparing it against null is always "
                + ("true" if node_text(op, sb) == "!=" else "false"),
                "note": node_text(be, sb),
                "help": "Remove the null comparison; the value is known to be non-null",
            }
        )
    return out

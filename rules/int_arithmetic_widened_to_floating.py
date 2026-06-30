# rule: Integer division or int*int arithmetic computed then widened to long/float/double loses precision or overflows; widen an operand first.
# (authored by RuleSmith from the description above)

# rule: Integer division or int*int arithmetic computed then widened to long/float/double loses precision or overflows; widen an operand first.
"""Flag int-typed `/` or `*` arithmetic that is computed in int and then widened to long/float/double (assignment target or cast), where no operand was widened first."""

from rulesmith.parse import parse, find, span, node_text

RULE = "int-arithmetic-widened-to-floating"
WIDE = {"long", "float", "double"}


def _unwrap(node):
    while node is not None and node.type == "parenthesized_expression":
        inner = node.named_children
        if not inner:
            break
        node = inner[-1]
    return node


def _wide_cast(node, sb):
    if node.type == "cast_expression":
        ty = node.child_by_field_name("type")
        if ty and node_text(ty, sb).strip() in WIDE:
            return True
    return False


def _is_wide(node, sb):
    """True if this expression is already computed in a wide type (so the
    arithmetic does NOT lose precision/overflow). Heuristic, name-based:
    identifiers/method calls/int literals are assumed int."""
    node = _unwrap(node)
    if node is None:
        return False
    if _wide_cast(node, sb):
        return True
    t = node.type
    if t in ("decimal_floating_point_literal", "hex_floating_point_literal"):
        return True
    txt = node_text(node, sb).strip()
    # floating literal like 1.0 / 2f / .5, or long literal like 10L
    body = txt.rstrip("lLfFdD")
    suffixed = (
        txt and txt[-1] in "lLfFdD" and body.replace(".", "").replace("_", "").isdigit()
    )
    floating = (
        "." in txt and txt.replace(".", "").replace("_", "").rstrip("fFdD").isdigit()
    )
    if suffixed or floating:
        return True
    if t == "binary_expression":
        lhs = node.child_by_field_name("left")
        r = node.child_by_field_name("right")
        return (lhs is not None and _is_wide(lhs, sb)) or (
            r is not None and _is_wide(r, sb)
        )
    if t == "unary_expression":
        op = node.child_by_field_name("operand")
        return op is not None and _is_wide(op, sb)
    return False


def _muldiv(v, sb):
    cands = []
    if v.type == "binary_expression":
        cands.append(v)
    cands.extend(b for b in find(v, "binary_expression") if b.id != v.id)
    for b in cands:
        op = b.child_by_field_name("operator")
        if op is not None and node_text(op, sb).strip() in ("/", "*"):
            return b
    return None


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    root = tree.root_node
    containers = []

    # context A: value assigned to a wide-typed local variable
    for d in find(root, "local_variable_declaration"):
        ty = d.child_by_field_name("type")
        if ty and node_text(ty, sb).strip() in WIDE:
            for vd in find(d, "variable_declarator"):
                v = vd.child_by_field_name("value")
                if v is not None:
                    containers.append(v)

    # context B: explicit widening cast around the arithmetic
    for c in find(root, "cast_expression"):
        ty = c.child_by_field_name("type")
        if ty and node_text(ty, sb).strip() in WIDE:
            val = c.child_by_field_name("value")
            if val is not None:
                containers.append(val)

    findings = []
    seen = set()
    for v in containers:
        if _is_wide(v, sb):  # an operand was widened first -> safe
            continue
        b = _muldiv(v, sb)
        if b is None:
            continue
        line, col, _, _ = span(b)
        if (line, col) in seen:
            continue
        seen.add((line, col))
        expr = node_text(b, sb).strip()
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "int arithmetic computed in int then widened to long/float/double",
                "note": f"`{expr}` evaluates in int (precision loss on `/`, overflow on `*`) before widening",
                "help": "widen an operand first, e.g. `(long)/(double) a * b` or `a / 2.0`",
                "judge": True,
            }
        )
    return findings

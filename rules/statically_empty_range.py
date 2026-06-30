# rule: Loop or range bounds that are statically empty (e.g. for(i=10;i<9;i++)) mean the body never executes.
# (authored by RuleSmith from the description above)

# rule: Loop or range bounds that are statically empty (e.g. for(i=10;i<9;i++)) mean the body never executes.
"""Flag for-loops whose static start value already fails the condition, so the body never runs."""

from rulesmith.parse import parse, find, span, node_text

RULE = "statically-empty-range"

_OPS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def _int_value(node, srcb):
    """Static integer value of a literal (or +/- unary literal), else None."""
    if node is None:
        return None
    if node.type == "decimal_integer_literal":
        try:
            return int(node_text(node, srcb).rstrip("lL").replace("_", ""))
        except ValueError:
            return None
    if node.type == "unary_expression":
        op = node.child_by_field_name("operator")
        v = _int_value(node.child_by_field_name("operand"), srcb)
        if v is None or op is None:
            return None
        return -v if node_text(op, srcb) == "-" else v
    return None


def _init_var(init, srcb):
    """(varname, start) from a `int i = N` or `i = N` for-init, else (None, None)."""
    if init is None:
        return None, None
    if init.type == "local_variable_declaration":
        decls = find(init, "variable_declarator")
        if len(decls) != 1:
            return None, None
        name = decls[0].child_by_field_name("name")
        if name is None:
            return None, None
        return node_text(name, srcb), _int_value(
            decls[0].child_by_field_name("value"), srcb
        )
    if init.type == "assignment_expression":
        left = init.child_by_field_name("left")
        if left is not None and left.type == "identifier":
            return node_text(left, srcb), _int_value(
                init.child_by_field_name("right"), srcb
            )
    return None, None


def analyze_source(src, file="<src>"):
    tree, srcb = parse(src)
    findings = []
    for fr in find(tree.root_node, "for_statement"):
        cond = fr.child_by_field_name("condition")
        if cond is None or cond.type != "binary_expression":
            continue
        var, start = _init_var(fr.child_by_field_name("init"), srcb)
        if var is None or start is None:
            continue
        op_node = cond.child_by_field_name("operator")
        left = cond.child_by_field_name("left")
        right = cond.child_by_field_name("right")
        op = node_text(op_node, srcb) if op_node is not None else None
        if op not in _OPS or left is None or right is None:
            continue
        if left.type == "identifier" and node_text(left, srcb) == var:
            bound = _int_value(right, srcb)
            empty = bound is not None and not _OPS[op](start, bound)
        elif right.type == "identifier" and node_text(right, srcb) == var:
            bound = _int_value(left, srcb)
            empty = bound is not None and not _OPS[op](bound, start)
        else:
            continue
        if empty:
            line, col = span(cond)[0], span(cond)[1]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "for-loop range is statically empty; body never executes",
                    "note": "with %s=%d at entry, condition `%s` is already false"
                    % (var, start, node_text(cond, srcb)),
                    "help": "remove the dead loop or fix the bounds",
                }
            )
    return findings

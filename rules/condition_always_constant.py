# rule: A condition whose boolean result is provably constant on all reaching paths makes a branch dead and signals a logic error.
# (authored by RuleSmith from the description above)

# rule: A condition whose boolean result is provably constant on all reaching paths makes a branch dead and signals a logic error.
"""Flag conditions whose boolean value is provably constant (dead branch)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "condition-always-constant"

_CMP = {"==", "!=", "<", ">", "<=", ">="}


def _strip(node):
    while node is not None and node.type == "parenthesized_expression":
        named = node.named_children
        if not named:
            break
        node = named[0]
    return node


def _lit(node, which):
    node = _strip(node)
    return node is not None and node.type == which


def _const_bool_locals(method, src_b):
    names = set()
    for decl in find(method, "local_variable_declaration"):
        t = decl.child_by_field_name("type")
        if t is None or node_text(t, src_b) != "boolean":
            continue
        for d in decl.named_children:
            if d.type != "variable_declarator":
                continue
            v = d.child_by_field_name("value")
            nm = d.child_by_field_name("name")
            if v is not None and nm is not None and v.type in ("true", "false"):
                names.add(node_text(nm, src_b))
    # a variable that is later reassigned is not provably constant
    for asn in find(method, "assignment_expression", "update_expression"):
        if asn.type == "assignment_expression":
            left = asn.child_by_field_name("left")
        else:
            left = asn.named_children[0] if asn.named_children else None
        if left is not None and left.type == "identifier":
            names.discard(node_text(left, src_b))
    return names


def _why(node, src_b, consts):
    node = _strip(node)
    if node is None:
        return None
    if node.type in ("true", "false"):
        return "boolean literal `%s` used as condition" % node.type
    if node.type == "unary_expression":
        op = node.child_by_field_name("operand")
        if op is not None and _why(op, src_b, consts):
            return "negation of a constant condition is itself constant"
    if node.type == "identifier" and node_text(node, src_b) in consts:
        return "`%s` is assigned a constant boolean and never reassigned" % node_text(
            node, src_b
        )
    if node.type == "binary_expression":
        op = node.child_by_field_name("operator")
        lhs = node.child_by_field_name("left")
        r = node.child_by_field_name("right")
        opt = node_text(op, src_b) if op is not None else ""
        if opt in _CMP and lhs is not None and r is not None:
            if lhs.type in ("identifier", "field_access") and r.type in (
                "identifier",
                "field_access",
            ):
                if node_text(lhs, src_b) == node_text(r, src_b):
                    val = (
                        "false"
                        if opt == "!="
                        else ("true" if opt == "==" else "constant")
                    )
                    return "self-comparison `%s` is always %s" % (
                        node_text(node, src_b),
                        val,
                    )
        if opt == "&&" and (_lit(lhs, "false") or _lit(r, "false")):
            return "`&&` with a constant `false` operand is always false"
        if opt == "||" and (_lit(lhs, "true") or _lit(r, "true")):
            return "`||` with a constant `true` operand is always true"
    return None


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    methods = find(tree.root_node, "method_declaration", "constructor_declaration")
    targets = methods if methods else [tree.root_node]
    for m in targets:
        consts = _const_bool_locals(m, src_b)
        for st in find(
            m,
            "if_statement",
            "while_statement",
            "do_statement",
            "for_statement",
            "ternary_expression",
        ):
            cond = st.child_by_field_name("condition")
            if cond is None:
                continue
            why = _why(cond, src_b, consts)
            if why is None:
                continue
            inner = _strip(cond)
            line, col, _, _ = span(inner)
            out.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Condition is provably constant; one branch is dead code.",
                    "note": why,
                    "help": "Remove the dead branch or fix the condition logic.",
                }
            )
    return out

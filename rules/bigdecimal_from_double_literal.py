# rule: Constructing BigDecimal from a double literal introduces representation error; use the String constructor or BigDecimal.valueOf.
# (authored by RuleSmith from the description above)

# rule: Constructing BigDecimal from a double literal introduces representation error; use the String constructor or BigDecimal.valueOf.
"""Flag new BigDecimal(<double literal>); prefer the String constructor or BigDecimal.valueOf."""

from rulesmith.parse import parse, find, span, node_text

RULE = "bigdecimal-from-double-literal"

_FLOAT_LITS = {"decimal_floating_point_literal", "hex_floating_point_literal"}


def _double_literal(node):
    # unwrap a leading +/- and report the float literal, if any
    if node is None:
        return None
    if node.type in _FLOAT_LITS:
        return node
    if node.type == "unary_expression":
        return _double_literal(node.child_by_field_name("operand"))
    return None


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for new in find(tree.root_node, "object_creation_expression"):
        tnode = new.child_by_field_name("type")
        if tnode is None or node_text(tnode, src_b).split(".")[-1] != "BigDecimal":
            continue
        args = new.child_by_field_name("arguments")
        if args is None:
            continue
        arg_nodes = list(args.named_children)
        if not arg_nodes:
            continue
        lit = _double_literal(arg_nodes[0])
        if lit is None:
            continue
        line, col, *_ = span(new)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "BigDecimal constructed from a double literal",
                "note": f"new BigDecimal({node_text(arg_nodes[0], src_b)}) inherits the double's representation error",
                "help": 'use new BigDecimal("...") or BigDecimal.valueOf(...)',
            }
        )
    return findings

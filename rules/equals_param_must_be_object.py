# rule: equals must take a single Object parameter; a narrower parameter type silently overloads rather than overrides Object.equals.
# (authored by RuleSmith from the description above)

# rule: equals must take a single Object parameter; a narrower parameter type silently overloads rather than overrides Object.equals.
"""equals must take a single Object parameter, not a narrower overload that hides Object.equals."""

from rulesmith.parse import parse, find, span, node_text

RULE = "equals-param-must-be-object"

_OBJECT = ("Object", "java.lang.Object")


def _params(method):
    p = method.child_by_field_name("parameters")
    if p is None:
        return []
    return [c for c in p.named_children if c.type == "formal_parameter"]


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration"):
        name_node = m.child_by_field_name("name")
        if name_node is None or node_text(name_node, src_b) != "equals":
            continue
        params = _params(m)
        if len(params) != 1:
            continue
        ptype_node = params[0].child_by_field_name("type")
        if ptype_node is None:
            continue
        ptype = node_text(ptype_node, src_b)
        if ptype in _OBJECT:
            continue
        line, col, *_ = span(name_node)
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"equals(...) declares parameter '{ptype}', not Object; this overloads rather than overrides Object.equals",
                "note": f"single parameter has type '{ptype}', expected Object",
                "help": "declare equals(Object o), then instanceof/cast inside; add @Override so the compiler catches the mistake",
            }
        )
    return out

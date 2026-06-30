# rule: An equals comparison (==, !=, or .equals) between provably unrelated types is always false and signals a logic error.
# (authored by RuleSmith from the description above)

# rule: An equals comparison (==, !=, or .equals) between provably unrelated types is always false and signals a logic error.
"""Flag ==/!=/.equals between provably unrelated types (always false/true)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "equals-between-incompatible-types"

# Primitives normalized to their wrapper so int==Integer is treated as same group.
_PRIM = {
    "int": "Integer",
    "long": "Long",
    "double": "Double",
    "float": "Float",
    "boolean": "Boolean",
    "char": "Character",
    "byte": "Byte",
    "short": "Short",
}
# Final / mutually-exclusive types: distinct names here can never be .equals/== equal.
_KNOWN = set(_PRIM.values()) | {"String"}


def _norm(t):
    t = t.split("<")[0].strip()
    return _PRIM.get(t, t)


def _var_types(method, src_b):
    types = {}
    for decl in find(method, "local_variable_declaration", "formal_parameter"):
        tnode = decl.child_by_field_name("type")
        if tnode is None:
            continue
        tname = _norm(node_text(tnode, src_b))
        nnode = decl.child_by_field_name("name")  # formal_parameter has name here
        if nnode is not None:
            types[node_text(nnode, src_b)] = tname
        for vd in find(decl, "variable_declarator"):  # local_variable_declaration
            vn = vd.child_by_field_name("name")
            if vn is not None:
                types[node_text(vn, src_b)] = tname
    return types


def _expr_type(node, types, src_b):
    if node is None:
        return None
    if node.type == "string_literal":
        return "String"
    if node.type == "identifier":
        return types.get(node_text(node, src_b))
    return None


def _incompatible(t1, t2):
    return t1 in _KNOWN and t2 in _KNOWN and t1 != t2


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        types = _var_types(method, src_b)

        for be in find(method, "binary_expression"):
            opn = be.child_by_field_name("operator")
            op = node_text(opn, src_b) if opn is not None else ""
            if op not in ("==", "!="):
                continue
            lt = _expr_type(be.child_by_field_name("left"), types, src_b)
            r = _expr_type(be.child_by_field_name("right"), types, src_b)
            if _incompatible(lt, r):
                line, col = span(be)[0], span(be)[1]
                always = "false" if op == "==" else "true"
                out.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"{op} between unrelated types {lt} and {r} is always {always}",
                        "note": f"left type {lt}, right type {r} are provably unrelated",
                        "help": "remove the comparison or fix the operand types",
                    }
                )

        for mi in find(method, "method_invocation"):
            nm = mi.child_by_field_name("name")
            if nm is None or node_text(nm, src_b) != "equals":
                continue
            args = mi.child_by_field_name("arguments")
            argn = list(args.named_children) if args is not None else []
            if len(argn) != 1:
                continue
            recv = _expr_type(mi.child_by_field_name("object"), types, src_b)
            arg = _expr_type(argn[0], types, src_b)
            if _incompatible(recv, arg):
                line, col = span(mi)[0], span(mi)[1]
                out.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f".equals between unrelated types {recv} and {arg} is always false",
                        "note": f"receiver type {recv}, argument type {arg} are provably unrelated",
                        "help": "these types can never be equal; fix the logic",
                    }
                )
    return out

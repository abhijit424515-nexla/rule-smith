# rule: A boxed type (Integer/Long/Boolean) that may be null must not be auto-unboxed in arithmetic, comparison, or condition contexts.
# (authored by RuleSmith from the description above)

# rule: A boxed type (Integer/Long/Boolean) that may be null must not be auto-unboxed in arithmetic, comparison, or condition contexts.
"""Flag auto-unboxing of a possibly-null boxed primitive in arithmetic/comparison/condition contexts."""

from rulesmith.parse import parse, find, span, node_text

RULE = "unboxing-of-possibly-null-boxed-primitive"

BOXED = {"Integer", "Long", "Boolean", "Short", "Byte", "Character", "Double", "Float"}
ARITH = {"+", "-", "*", "/", "%"}
COMPARE = {"<", "<=", ">", ">="}


def _field(node, name):
    return node.child_by_field_name(name) if node is not None else None


def _strip_paren(node):
    while node is not None and node.type == "parenthesized_expression":
        kids = node.named_children
        node = kids[0] if kids else None
    return node


def _ident_is(node, names, b):
    return (
        node is not None and node.type == "identifier" and node_text(node, b) in names
    )


def _possibly_null_boxed(method, b):
    # name -> True if it may be null (null init, no init, or assigned null)
    may = {}
    for decl in find(method, "local_variable_declaration"):
        t = _field(decl, "type")
        if t is None or node_text(t, b) not in BOXED:
            continue
        for vd in find(decl, "variable_declarator"):
            nm = _field(vd, "name")
            if nm is None:
                continue
            name = node_text(nm, b)
            val = _field(vd, "value")
            may[name] = (val is None) or (val.type == "null_literal")
    for asg in find(method, "assignment_expression"):
        left = _field(asg, "left")
        right = _field(asg, "right")
        if left is not None and left.type == "identifier" and node_text(left, b) in may:
            if right is not None and right.type == "null_literal":
                may[node_text(left, b)] = True
    return {n for n, v in may.items() if v}


def _mk(node, b, ctx, op):
    line, col = span(node)[0], span(node)[1]
    nm = node_text(node, b)
    return {
        "rule": RULE,
        "file": None,
        "line": line,
        "col": col,
        "message": f"Possibly-null boxed value '{nm}' auto-unboxed in {ctx} context",
        "note": f"'{nm}' may be null (declared with no/null initializer or assigned null); operator '{op}' forces unboxing -> potential NullPointerException",
        "help": f"Null-check before unboxing (e.g. if ({nm} != null) ...) or supply a default.",
        "judge": True,
    }


def _unbox_sites(method, b, names):
    out = []
    for be in find(method, "binary_expression"):
        op = _field(be, "operator")
        if op is None:
            continue
        opt = node_text(op, b)
        if opt not in ARITH and opt not in COMPARE:
            continue
        for side in (_field(be, "left"), _field(be, "right")):
            if _ident_is(side, names, b):
                out.append(_mk(side, b, "arithmetic/comparison", opt))
    for st in find(method, "if_statement", "while_statement", "do_statement"):
        cond = _strip_paren(_field(st, "condition"))
        if _ident_is(cond, names, b):
            out.append(_mk(cond, b, "condition", "if/while"))
    for tern in find(method, "ternary_expression"):
        cond = _strip_paren(_field(tern, "condition"))
        if _ident_is(cond, names, b):
            out.append(_mk(cond, b, "condition", "?:"))
    for un in find(method, "unary_expression"):
        op = _field(un, "operator")
        if op is not None and node_text(op, b) == "!":
            operand = _strip_paren(_field(un, "operand"))
            if _ident_is(operand, names, b):
                out.append(_mk(operand, b, "condition", "!"))
    return out


def analyze_source(src, file="<src>"):
    tree, b = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        names = _possibly_null_boxed(method, b)
        if not names:
            continue
        seen = set()
        for f in _unbox_sites(method, b, names):
            key = (f["line"], f["col"])
            if key in seen:
                continue
            seen.add(key)
            f["file"] = file
            findings.append(f)
    return findings

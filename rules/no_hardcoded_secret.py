# rule: do not assign a string literal to a variable or field named password, passwd, secret, apikey, or token

from rulesmith.parse import parse, find, span, node_text

RULE = "no-hardcoded-secret"

_NAMES = {"password", "passwd", "secret", "apikey", "token"}


def _target_name(node, src_bytes):
    # identifier on the left of an assignment, or the field part of `this.token`
    if node.type == "identifier":
        return node_text(node, src_bytes)
    if node.type == "field_access":
        fld = node.child_by_field_name("field")
        return node_text(fld, src_bytes) if fld is not None else None
    return None


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    # variable/field declarations: `String token = "..."`
    for vd in find(tree.root_node, "variable_declarator"):
        name = vd.child_by_field_name("name")
        value = vd.child_by_field_name("value")
        if name is None or value is None or value.type != "string_literal":
            continue
        ident = node_text(name, src_bytes)
        if ident.lower() not in _NAMES:
            continue
        line, col, _el, _ec = span(vd)
        findings.append(_finding(file, line, col, ident, vd, src_bytes))
    # plain assignments: `token = "..."` / `this.token = "..."`
    for ae in find(tree.root_node, "assignment_expression"):
        left = ae.child_by_field_name("left")
        right = ae.child_by_field_name("right")
        if left is None or right is None or right.type != "string_literal":
            continue
        ident = _target_name(left, src_bytes)
        if ident is None or ident.lower() not in _NAMES:
            continue
        line, col, _el, _ec = span(ae)
        findings.append(_finding(file, line, col, ident, ae, src_bytes))
    return findings


def _finding(file, line, col, ident, node, src_bytes):
    return {
        "rule": RULE,
        "file": file,
        "line": line,
        "col": col,
        "message": f"string literal assigned to sensitive name '{ident}'",
        "note": node_text(node, src_bytes).strip()[:80],
        "help": "Load secrets from env/config/secret manager, never hardcode them.",
    }

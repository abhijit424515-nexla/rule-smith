# rule: Flag sensitive Cookie creation without setSecure(true)/setHttpOnly(true).
# (authored by RuleSmith from the description above)

# rule: Flag sensitive Cookie creation without setSecure(true)/setHttpOnly(true).
"""Cookie created without setSecure(true)/setHttpOnly(true)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "insecure-cookie-flags"


def _calls_true(root, src_b, var, method):
    for inv in find(root, "method_invocation"):
        obj = inv.child_by_field_name("object")
        nm = inv.child_by_field_name("name")
        args = inv.child_by_field_name("arguments")
        if obj is None or nm is None:
            continue
        if node_text(obj, src_b) == var and node_text(nm, src_b) == method:
            if args is not None and "true" in node_text(args, src_b):
                return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node
    findings = []
    for obj in find(root, "object_creation_expression"):
        t = obj.child_by_field_name("type")
        if t is None:
            continue
        tname = node_text(t, src_b)
        if tname != "Cookie" and not tname.endswith(".Cookie"):
            continue
        decl = obj.parent
        if decl is None or decl.type != "variable_declarator":
            continue
        nm = decl.child_by_field_name("name")
        if nm is None:
            continue
        var = node_text(nm, src_b)
        secure = _calls_true(root, src_b, var, "setSecure")
        http = _calls_true(root, src_b, var, "setHttpOnly")
        if secure and http:
            continue
        missing = []
        if not secure:
            missing.append("setSecure(true)")
        if not http:
            missing.append("setHttpOnly(true)")
        line, col, _, _ = span(obj)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Cookie '{var}' created without {' and '.join(missing)}",
                "note": f"new Cookie(...) assigned to '{var}'; missing {', '.join(missing)}",
                "help": "Call cookie.setSecure(true) and cookie.setHttpOnly(true) before sending the cookie.",
            }
        )
    return findings

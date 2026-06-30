# rule: do not assign a variable to itself

from rulesmith.parse import parse, find, span, node_text

RULE = "no-self-assignment"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for ae in find(tree.root_node, "assignment_expression"):
        op = ae.child_by_field_name("operator")
        if op is None or node_text(op, src_bytes) != "=":
            continue
        left = ae.child_by_field_name("left")
        right = ae.child_by_field_name("right")
        if left is None or right is None:
            continue
        # only flag simple lvalues (a name or a field access like this.x),
        # so call-bearing RHS (a = a()) and index exprs are out of scope
        if left.type not in ("identifier", "field_access"):
            continue
        if right.type not in ("identifier", "field_access"):
            continue
        lt = node_text(left, src_bytes).strip()
        rt = node_text(right, src_bytes).strip()
        if lt != rt:
            continue
        line, col, _el, _ec = span(ae)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"variable '{lt}' assigned to itself",
                "note": node_text(ae, src_bytes).strip()[:80],
                "help": "Remove the redundant assignment, or fix the typo on either side.",
            }
        )
    return findings

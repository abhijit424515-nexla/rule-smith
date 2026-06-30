from rulesmith.parse import parse, find, node_text, span

RULE = "no-assign-in-condition"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    seen = set()
    for stmt in find(tree.root_node, "if_statement", "while_statement"):
        cond = stmt.child_by_field_name("condition")
        if cond is None:
            continue
        for assign in find(cond, "assignment_expression"):
            if assign.id in seen:
                continue
            seen.add(assign.id)
            line, col, _, _ = span(assign)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "assignment inside if/while condition",
                    "note": node_text(assign, src_bytes).splitlines()[0],
                    "help": "Do not assign inside a condition; it is almost always a typo for '=='. Move the assignment to its own statement, or use '==' to compare.",
                }
            )
    return findings

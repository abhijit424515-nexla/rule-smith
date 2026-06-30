# rule: do not call printStackTrace; use a logger instead

from rulesmith.parse import parse, find, node_text, span

RULE = "no-printstacktrace"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for call in find(tree.root_node, "method_invocation"):
        name = call.child_by_field_name("name")
        if name is None:
            continue
        if node_text(name, src_bytes) != "printStackTrace":
            continue
        line, col, _, _ = span(call)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Do not call printStackTrace(); use a logger instead.",
                "note": node_text(call, src_bytes),
                "help": 'Replace e.printStackTrace() with logger.error("message", e).',
            }
        )
    return findings

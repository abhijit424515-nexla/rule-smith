# rule: do not call System.exit

from rulesmith.parse import parse, find, node_text, span

RULE = "no-system-exit"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for call in find(tree.root_node, "method_invocation"):
        obj = call.child_by_field_name("object")
        name = call.child_by_field_name("name")
        if obj is None or name is None:
            continue
        if (
            node_text(obj, src_bytes) == "System"
            and node_text(name, src_bytes) == "exit"
        ):
            line, col, _, _ = span(call)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Do not call System.exit().",
                    "note": node_text(call, src_bytes),
                    "help": "Throw an exception or return a status code instead of terminating the JVM directly.",
                }
            )
    return findings

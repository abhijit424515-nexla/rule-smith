# rule: do not throw exceptions from within a finally block

from rulesmith.parse import parse, find, node_text, span

RULE = "no-throw-in-finally"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for finally_clause in find(tree.root_node, "finally_clause"):
        for throw in find(finally_clause, "throw_statement"):
            line, col, _, _ = span(throw)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "throw inside finally block",
                    "note": node_text(throw, src_bytes).splitlines()[0],
                    "help": "Do not throw from a finally block; it discards any exception or return from try/catch. Move the throw out or handle the error locally.",
                }
            )
    return findings

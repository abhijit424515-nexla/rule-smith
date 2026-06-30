# rule: a method must not have more than 5 return statements

from rulesmith.parse import parse, find, span, node_text

RULE = "max-return-statements"
MAX_RETURNS = 5


def _method_name(method_ts, src_bytes):
    name = method_ts.child_by_field_name("name")
    return node_text(name, src_bytes) if name is not None else "<method>"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        body = method.child_by_field_name("body")
        if body is None:
            continue
        # ponytail: counts all descendant returns incl. lambdas/anon classes;
        # acceptable for a per-method cap. Scope to nearest method if false positives appear.
        returns = find(body, "return_statement")
        count = len(returns)
        if count > MAX_RETURNS:
            line, col, _, _ = span(method)
            name = _method_name(method, src_bytes)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"Method '{name}' has {count} return statements (max {MAX_RETURNS}).",
                    "note": f"{count} return_statement nodes found in method body.",
                    "help": "Reduce return statements; extract helpers or use a single result variable.",
                }
            )
    return findings

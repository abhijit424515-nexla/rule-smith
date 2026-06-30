# rule: do not nest a ternary conditional expression inside another ternary

from rulesmith.parse import parse, find, span, node_text

RULE = "no-nested-ternary"


def _has_ancestor_ternary(node):
    p = node.parent
    while p is not None:
        if p.type == "ternary_expression":
            return True
        p = p.parent
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for t in find(tree.root_node, "ternary_expression"):
        # Only report an outermost ternary so a single nesting tree counts once.
        if _has_ancestor_ternary(t):
            continue
        # A nested ternary appears as a descendant ternary_expression.
        if not any(c is not t for c in find(t, "ternary_expression")):
            continue
        line, col, _el, _ec = span(t)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "nested ternary conditional expression",
                "note": node_text(t, src_bytes).strip()[:80],
                "help": "Extract the inner ?: into an if/else or a named variable.",
            }
        )
    return findings

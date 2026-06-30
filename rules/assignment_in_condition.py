# rule: An assignment used as the controlling expression of an if/while/for is almost always a mistaken == comparison; conditions must be genuine boolean expressions.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "assignment-in-condition"


def _unwrap(node):
    while node is not None and node.type == "parenthesized_expression":
        inner = None
        for c in node.named_children:
            inner = c
        node = inner
    return node


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for stmt in find(
        tree.root_node, "if_statement", "while_statement", "for_statement"
    ):
        cond = stmt.child_by_field_name("condition")
        expr = _unwrap(cond)
        if expr is None or expr.type != "assignment_expression":
            continue
        op = expr.child_by_field_name("operator")
        if op is None or node_text(op, src_bytes) != "=":
            continue
        line, col, _, _ = span(expr)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Assignment used as a condition; did you mean '=='?",
                "note": node_text(cond, src_bytes),
                "help": "Use a boolean comparison ('==') or move the assignment out of the condition.",
            }
        )
    return findings

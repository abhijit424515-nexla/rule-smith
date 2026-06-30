# rule: A return or throw inside a finally block discards any pending exception or return value from the try/catch.
# (authored by RuleSmith from the description above)

# rule: A return or throw inside a finally block discards any pending exception or return value from the try/catch.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "return-throw-in-finally"

# Returns/throws inside a nested lambda, anonymous/local class, or nested method
# belong to that inner scope and do NOT discard the outer try's pending result.
_PRUNE = {
    "lambda_expression",
    "class_body",
    "method_declaration",
    "constructor_declaration",
}


def _abrupt_in_finally(block, src):
    """Yield (kind, node) for return/throw directly governed by this finally block."""
    out = []

    def walk(n):
        for c in n.children:
            if c.type in _PRUNE:
                continue
            if c.type == "return_statement":
                out.append(("return", c))
            elif c.type == "throw_statement":
                out.append(("throw", c))
            walk(c)

    walk(block)
    return out


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for fin in find(tree.root_node, "finally_clause"):
        block = fin.child_by_field_name("body") or fin.children[-1]
        for kind, node in _abrupt_in_finally(block, src_bytes):
            line, col, _, _ = span(node)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"'{kind}' inside finally discards any pending exception or return from try/catch.",
                    "note": node_text(node, src_bytes).strip(),
                    "help": "Remove the return/throw from finally; let the try/catch result propagate.",
                }
            )
    return findings

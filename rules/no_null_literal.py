# rule: Use of the null literal must be flagged; nullable references break type safety and absence should be modeled with Optional.
# (authored by RuleSmith from the description above)

# rule: Use of the null literal must be flagged; nullable references break type safety and absence should be modeled with Optional.
"""Flag every use of the null literal; model absence with Optional instead."""

from rulesmith.parse import parse, find, span

RULE = "no-null-literal"


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for node in find(tree.root_node, "null_literal"):
        line, col, _, _ = span(node)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "use of null literal",
                "note": "null at %s:%d:%d" % (file, line, col),
                "help": "model absence with Optional (Optional.empty / Optional.ofNullable)",
            }
        )
    return findings

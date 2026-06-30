# rule: A method's cyclomatic complexity (decision points plus 1) must stay at or below a configured threshold.
# (authored by RuleSmith from the description above)

# rule: A method's cyclomatic complexity (decision points plus 1) must stay at or below a configured threshold.
"""Flag methods whose cyclomatic complexity exceeds a configured threshold."""

from rulesmith.parse import parse, find, span, node_text

RULE = "cyclomatic-complexity-too-high"
THRESHOLD = 10  # ponytail: module constant; expose as config when a caller actually needs per-run tuning

# Each of these tree-sitter node types is one decision point (branch in the CFG).
DECISION_TYPES = (
    "if_statement",
    "while_statement",
    "do_statement",
    "for_statement",
    "enhanced_for_statement",
    "catch_clause",
    "ternary_expression",
)


def _complexity(method, src_b):
    # ponytail: find() descends into nested/anon-class methods too, so their
    # branches fold into the enclosing method's count. Acceptable over-count;
    # split per-method if nested classes ever matter.
    n = 1
    for t in DECISION_TYPES:
        n += len(find(method, t))
    # switch: each `case` label adds a path; `default` does not.
    for sl in find(method, "switch_label"):
        if node_text(sl, src_b).strip().startswith("case"):
            n += 1
    # short-circuit boolean operators each introduce a branch.
    for be in find(method, "binary_expression"):
        op = be.child_by_field_name("operator")
        if op is not None and node_text(op, src_b) in ("&&", "||"):
            n += 1
    return n


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        c = _complexity(m, src_b)
        if c <= THRESHOLD:
            continue
        name = m.child_by_field_name("name")
        anchor = name if name is not None else m
        line, col = span(anchor)[0], span(anchor)[1]
        nm = node_text(name, src_b) if name is not None else "<init>"
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"method '{nm}' has cyclomatic complexity {c} (threshold {THRESHOLD})",
                "note": f"{c - 1} decision points + 1 = {c}",
                "help": f"extract helpers or simplify branching to bring complexity to <= {THRESHOLD}",
            }
        )
    return findings

# rule: do not compare a boolean to a boolean literal such as == true or != false

from rulesmith.parse import parse, find, span, node_text

RULE = "no-boolean-literal-comparison"

_LITERALS = {"true", "false"}


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for be in find(tree.root_node, "binary_expression"):
        op = be.child_by_field_name("operator")
        if op is None or node_text(op, src_bytes) not in ("==", "!="):
            continue
        left = be.child_by_field_name("left")
        right = be.child_by_field_name("right")
        # tree-sitter-java exposes boolean literals as 'true'/'false' node types,
        # so this never matches a string_literal like "true" or an identifier.
        lit = next(
            (s for s in (left, right) if s is not None and s.type in _LITERALS),
            None,
        )
        if lit is None:
            continue
        word = lit.type
        line, col, _el, _ec = span(be)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"comparison of boolean to literal '{word}'",
                "note": node_text(be, src_bytes).strip()[:80],
                "help": "Drop the comparison: use the boolean directly (or negate with '!').",
            }
        )
    return findings

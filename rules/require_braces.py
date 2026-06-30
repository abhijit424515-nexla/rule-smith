# rule: if, else, for, and while bodies must always use braces, never a single statement without a block

from rulesmith.parse import parse, find, span, node_text

RULE = "require-braces"


def _check_body(body, kw, src_bytes, file, findings):
    """Flag a control-flow body that is not a brace block."""
    if body is None:
        return
    if body.type == "block":
        return
    # `else if` chains are legal: the else body is itself an if_statement.
    if kw == "else" and body.type == "if_statement":
        return
    line, col, _el, _ec = span(body)
    findings.append(
        {
            "rule": RULE,
            "file": file,
            "line": line,
            "col": col,
            "message": f"{kw} body must use braces",
            "note": node_text(body, src_bytes).strip()[:80],
            "help": f"Wrap the {kw} body in {{ }}.",
        }
    )


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for node in find(tree.root_node, "if_statement"):
        _check_body(
            node.child_by_field_name("consequence"), "if", src_bytes, file, findings
        )
        _check_body(
            node.child_by_field_name("alternative"), "else", src_bytes, file, findings
        )
    for node in find(tree.root_node, "while_statement"):
        _check_body(
            node.child_by_field_name("body"), "while", src_bytes, file, findings
        )
    for node in find(tree.root_node, "for_statement"):
        _check_body(node.child_by_field_name("body"), "for", src_bytes, file, findings)
    for node in find(tree.root_node, "enhanced_for_statement"):
        _check_body(node.child_by_field_name("body"), "for", src_bytes, file, findings)
    return findings

from rulesmith.parse import parse, find, span, node_text

RULE = "no-empty-if-while-body"

_COMMENTS = {"line_comment", "block_comment"}


def _is_empty(body):
    if body is None:
        return False
    if body.type == ";":  # bare empty statement: if (x);
        return True
    if body.type == "block":  # { } with no real statements
        return all(c.type in _COMMENTS for c in body.named_children)
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for stmt in find(tree.root_node, "if_statement", "while_statement"):
        kind = "if" if stmt.type == "if_statement" else "while"
        field = "consequence" if kind == "if" else "body"
        body = stmt.child_by_field_name(field)
        if not _is_empty(body):
            continue
        line, col, _, _ = span(stmt)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"{kind} statement has an empty body",
                "note": node_text(body, src_bytes),
                "help": f"Add statements to the {kind} body or remove the {kind} statement.",
            }
        )
    return findings

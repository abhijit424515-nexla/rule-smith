from rulesmith.parse import parse, find, node_text, span

RULE = "no-system-out-err"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for call in find(tree.root_node, "method_invocation"):
        obj = call.child_by_field_name("object")
        if obj is None or obj.type != "field_access":
            continue
        base = obj.child_by_field_name("object")
        field = obj.child_by_field_name("field")
        if base is None or field is None:
            continue
        if node_text(base, src_bytes) != "System":
            continue
        stream = node_text(field, src_bytes)
        if stream not in ("out", "err"):
            continue
        line, col, _, _ = span(call)
        findings.append({
            "rule": RULE,
            "file": file,
            "line": line,
            "col": col,
            "message": "Do not use System." + stream + " for logging; use a logger.",
            "note": node_text(call, src_bytes),
            "help": 'Replace System.' + stream + '.println(...) with logger.info/error(...).',
        })
    return findings

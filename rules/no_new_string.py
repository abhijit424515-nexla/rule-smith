from rulesmith.parse import parse, find, span, node_text

RULE = "no-new-string"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for node in find(tree.root_node, "object_creation_expression"):
        type_node = node.child_by_field_name("type")
        if type_node is None:
            continue
        # ponytail: match simple `String`; `java.lang.String` is scoped_type_identifier, rare enough to skip
        if node_text(type_node, src_bytes) != "String":
            continue
        line, col = span(node)[0], span(node)[1]
        findings.append({
            "rule": RULE,
            "file": file,
            "line": line,
            "col": col,
            "message": "do not use the new String(...) constructor; use the string literal directly",
            "note": node_text(node, src_bytes),
            "help": "Replace `new String(\"x\")` with the literal `\"x\"`; the constructor allocates a needless extra object.",
        })
    return findings

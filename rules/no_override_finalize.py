from rulesmith.parse import parse, find, node_text, span

RULE = "no-override-finalize"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        name_node = m.child_by_field_name("name")
        if name_node is None:
            continue
        if node_text(name_node, src_bytes) != "finalize":
            continue
        # Object.finalize() takes no parameters; an override must match that signature.
        params = m.child_by_field_name("parameters")
        param_count = 0
        if params is not None:
            param_count = len(find(params, "formal_parameter"))
        if param_count != 0:
            continue
        line, col, _, _ = span(name_node)
        findings.append({
            "rule": RULE,
            "file": file,
            "line": line,
            "col": col,
            "message": "Do not override Object.finalize().",
            "note": node_text(name_node, src_bytes),
            "help": "finalize() is deprecated and unreliable; use try-with-resources, Closeable, or java.lang.ref.Cleaner instead.",
        })
    return findings

# rule: do not use double-brace initialization (an anonymous subclass with an instance initializer block)

from rulesmith.parse import parse, find, span, node_text

RULE = "no-double-brace-init"


def analyze_source(src, file="<src>"):
    """Flag double-brace initialization: an anonymous subclass (object
    creation with a class body) whose body contains an instance initializer
    block. In tree-sitter-java that initializer is a `block` node sitting as a
    direct child of the `class_body`."""
    tree, src_bytes = parse(src)
    findings = []
    for obj in find(tree.root_node, "object_creation_expression"):
        class_body = next((c for c in obj.children if c.type == "class_body"), None)
        if class_body is None:
            continue
        # An instance initializer is a bare `block` directly inside the body
        # (method bodies are nested under method_declaration, so they don't
        # show up here).
        init = next((c for c in class_body.children if c.type == "block"), None)
        if init is None:
            continue
        line, col, _, _ = span(obj)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Do not use double-brace initialization.",
                "note": node_text(init, src_bytes)[:120],
                "help": "Replace the anonymous subclass + instance initializer "
                "with explicit setup (e.g. Map.of/List.of, or a local var with "
                "normal add/put calls).",
            }
        )
    return findings

# rule: do not use legacy classes Vector, Hashtable, Stack, or StringBuffer; use modern equivalents

from rulesmith.parse import parse, find, node_text, span

RULE = "no-legacy-collections"

# Legacy class name -> modern replacement.
LEGACY = {
    "Vector": "ArrayList",
    "Hashtable": "HashMap",
    "Stack": "ArrayDeque",
    "StringBuffer": "StringBuilder",
}


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    # type_identifier covers declarations, params, generics, and `new T(...)`.
    # Import statements use scoped/identifier nodes, so they are not matched here.
    for node in find(tree.root_node, "type_identifier"):
        name = node_text(node, src_bytes)
        replacement = LEGACY.get(name)
        if replacement is None:
            continue
        line, col, _, _ = span(node)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Legacy class '{name}' used; prefer {replacement}.",
                "note": name,
                "help": f"Replace {name} with {replacement} (or another modern equivalent).",
            }
        )
    return findings

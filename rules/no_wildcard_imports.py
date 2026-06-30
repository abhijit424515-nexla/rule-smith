# rule: do not use wildcard imports (import statements ending in .*)

from rulesmith.parse import parse, find, span, node_text

RULE = "no-wildcard-imports"


def analyze_source(src, file="<src>"):
    findings = []
    tree, src_bytes = parse(src)

    for imp in find(tree.root_node, "import_declaration"):
        if not any(c.type == "asterisk" for c in imp.children):
            continue
        line, col, _, _ = span(imp)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Wildcard import; import each type explicitly",
                "note": node_text(imp, src_bytes),
                "help": "Replace the '.*' import with explicit single-type imports",
            }
        )

    return findings

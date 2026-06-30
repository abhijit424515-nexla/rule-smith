# rule: instance fields must not be both public and non-final

from rulesmith.parse import parse, find, span, node_text

RULE = "no-public-non-final-instance-field"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for fd in find(tree.root_node, "field_declaration"):
        mods = None
        for c in fd.children:
            if c.type == "modifiers":
                mods = c
                break
        if mods is None:
            continue
        words = {node_text(c, src_bytes) for c in mods.children}
        if "public" in words and "static" not in words and "final" not in words:
            line, col, _, _ = span(fd)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Instance field must not be both public and non-final",
                    "note": node_text(fd, src_bytes).strip(),
                    "help": "Make the field final, or reduce its visibility below public.",
                }
            )
    return findings

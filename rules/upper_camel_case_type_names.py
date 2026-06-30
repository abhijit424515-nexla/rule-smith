# rule: class and interface names must be UpperCamelCase (PascalCase)

from rulesmith.parse import parse, find, node_text, span

RULE = "upper-camel-case-type-names"


def _is_upper_camel(name):
    # UpperCamelCase: starts uppercase, only letters/digits, no underscores/$.
    if not name or not name[0].isupper():
        return False
    if not name.isalnum():  # rejects '_', '$', etc.
        return False
    return True


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for decl in find(tree.root_node, "class_declaration", "interface_declaration"):
        name_node = decl.child_by_field_name("name")
        if name_node is None:
            continue
        name = node_text(name_node, src_bytes)
        if _is_upper_camel(name):
            continue
        kind = "interface" if decl.type == "interface_declaration" else "class"
        line, col, _, _ = span(name_node)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "%s name '%s' is not UpperCamelCase" % (kind, name),
                "note": node_text(name_node, src_bytes),
                "help": "Rename '%s' to UpperCamelCase, e.g. start with a capital "
                "letter and drop underscores." % name,
            }
        )
    return findings

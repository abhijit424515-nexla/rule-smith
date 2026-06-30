# rule: static fields must be declared final

from rulesmith.parse import parse, find, span, node_text

RULE = "static-fields-final"


def _modifiers(field_node):
    for child in field_node.children:
        if child.type == "modifiers":
            return {m.type for m in child.children} | {
                node_text(m, b"") for m in child.children
            }
    return set()


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for field in find(tree.root_node, "field_declaration"):
        mods = set()
        for child in field.children:
            if child.type == "modifiers":
                for m in child.children:
                    mods.add(node_text(m, src_bytes))
        if "static" not in mods or "final" in mods:
            continue
        decl = field.child_by_field_name("declarator")
        name = None
        if decl is not None:
            name_node = decl.child_by_field_name("name")
            if name_node is not None:
                name = node_text(name_node, src_bytes)
        line, col, _, _ = span(field)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "static field '%s' must be declared final" % (name or "?"),
                "note": node_text(field, src_bytes).strip(),
                "help": "Add 'final' to the static field, or make it an instance field.",
            }
        )
    return findings

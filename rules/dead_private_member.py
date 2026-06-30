# rule: Private methods and fields that are never referenced anywhere in the compilation scope are dead and should be removed.
# (authored by RuleSmith from the description above)

# rule: Private methods and fields that are never referenced anywhere in the compilation scope are dead and should be removed.
"""Dead private members: private methods/fields with zero references anywhere in the file."""

from rulesmith.parse import parse, find, span, node_text

RULE = "dead-private-member"


def _is_private(node, src_b):
    # immediate-child modifiers only; avoid descendant nested decls
    for c in node.children:
        if c.type == "modifiers" and "private" in node_text(c, src_b).split():
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node

    # name -> total identifier occurrences across the whole compilation unit.
    # Call sites (method_invocation.name), reads, and field_access.field are all
    # identifier nodes, so a referenced member appears >1 time (decl + use).
    # ponytail: name-based, no type resolution; judge=True lets --judge filter
    # reflection/serialization/JNI false positives.
    counts = {}
    for ident in find(root, "identifier"):
        t = node_text(ident, src_b)
        counts[t] = counts.get(t, 0) + 1

    findings = []

    for m in find(root, "method_declaration"):
        if not _is_private(m, src_b):
            continue
        name_node = m.child_by_field_name("name")
        if name_node is None:
            continue
        name = node_text(name_node, src_b)
        if counts.get(name, 0) <= 1:
            line, col, *_ = span(name_node)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"private method '{name}' is never referenced",
                    "note": f"identifier '{name}' appears only at its declaration",
                    "help": "remove the unused private method",
                    "judge": True,
                }
            )

    for fd in find(root, "field_declaration"):
        if not _is_private(fd, src_b):
            continue
        for decl in find(fd, "variable_declarator"):
            name_node = decl.child_by_field_name("name")
            if name_node is None:
                continue
            name = node_text(name_node, src_b)
            if counts.get(name, 0) <= 1:
                line, col, *_ = span(name_node)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"private field '{name}' is never referenced",
                        "note": f"identifier '{name}' appears only at its declaration",
                        "help": "remove the unused private field",
                        "judge": True,
                    }
                )

    return findings

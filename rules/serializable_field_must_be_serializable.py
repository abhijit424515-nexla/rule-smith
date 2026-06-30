# rule: Every non-transient instance field of a Serializable class must itself be Serializable (or transient/Externalizable-handled), else serialization throws at runtime.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "serializable-field-must-be-serializable"


def _class_name(c, src):
    n = c.child_by_field_name("name")
    return node_text(n, src) if n is not None else ""


def _impls_serializable(c, src):
    # only the class's OWN super_interfaces (direct child), not a nested class's
    for ch in c.children:
        if ch.type == "super_interfaces":
            return "Serializable" in node_text(ch, src)
    return False


def _base_type_name(tnode, src):
    # peel array dimensions, then peel generic to its base name
    t = tnode
    while t is not None and t.type == "array_type":
        t = t.child_by_field_name("element")
    if t is None:
        return ""
    if t.type == "generic_type":
        if t.named_children:
            return node_text(t.named_children[0], src)
        return node_text(t, src)
    return node_text(t, src)


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    root = tree.root_node
    findings = []

    classes = find(root, "class_declaration")
    # map declared-in-file class name -> is it Serializable
    serial = {}
    for c in classes:
        serial[_class_name(c, sb)] = _impls_serializable(c, sb)

    for c in classes:
        if not _impls_serializable(c, sb):
            continue
        cname = _class_name(c, sb)
        body = c.child_by_field_name("body")
        if body is None:
            continue
        for fd in body.named_children:
            if fd.type != "field_declaration":
                continue
            mods = ""
            for ch in fd.children:
                if ch.type == "modifiers":
                    mods = node_text(ch, sb)
            if "transient" in mods or "static" in mods:
                continue
            tnode = fd.child_by_field_name("type")
            if tnode is None:
                continue
            tname = _base_type_name(tnode, sb)
            # only flag types declared in this file that are NOT Serializable;
            # primitives / library types (String, ...) are assumed serializable
            if tname not in serial or serial[tname]:
                continue
            decl = fd.child_by_field_name("declarator")
            if decl is None:
                decls = [
                    x for x in fd.named_children if x.type == "variable_declarator"
                ]
                decl = decls[0] if decls else fd
            namenode = (
                decl.child_by_field_name("name")
                if decl.type == "variable_declarator"
                else None
            )
            anchor = namenode if namenode is not None else fd
            line, col, _, _ = span(anchor)
            fname = node_text(namenode, sb) if namenode is not None else "<field>"
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": (
                        "Field '%s' of Serializable class '%s' has non-Serializable type '%s'"
                        % (fname, cname, tname)
                    ),
                    "note": "%s is declared in this unit and does not implement Serializable"
                    % tname,
                    "help": "Make %s implement Serializable, or mark the field transient."
                    % tname,
                }
            )

    return findings

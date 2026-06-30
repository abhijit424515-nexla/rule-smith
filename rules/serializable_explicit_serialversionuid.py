# rule: Classes implementing Serializable should declare an explicit private static final long serialVersionUID to avoid silent deserialization incompatibilities.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "serializable-explicit-serialversionuid"


def _implements_serializable(cls, src):
    iface = cls.child_by_field_name("interfaces")
    if iface is None:
        return False
    for t in find(iface, "type_identifier", "scoped_type_identifier"):
        name = node_text(t, src).split(".")[-1]
        if name == "Serializable":
            return True
    return False


def _has_serialversionuid(cls, src):
    body = cls.child_by_field_name("body")
    if body is None:
        return False
    for fld in body.named_children:
        if fld.type != "field_declaration":
            continue
        mods = "".join(node_text(m, src) for m in fld.children if m.type == "modifiers")
        if not ("private" in mods and "static" in mods and "final" in mods):
            continue
        ftype = fld.child_by_field_name("type")
        if ftype is None or node_text(ftype, src) != "long":
            continue
        for vd in find(fld, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None and node_text(nm, src) == "serialVersionUID":
                return True
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        if not _implements_serializable(cls, sb):
            continue
        if _has_serialversionuid(cls, sb):
            continue
        name = cls.child_by_field_name("name")
        line, col, _, _ = span(name if name is not None else cls)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Serializable class missing explicit serialVersionUID",
                "note": node_text(name, sb) if name is not None else "<class>",
                "help": "Declare 'private static final long serialVersionUID = 1L;'",
            }
        )
    return findings

# rule: Classes implementing Serializable should declare an explicit private static final long serialVersionUID to avoid silent deserialization incompatibilities.
# (authored by RuleSmith from the description above)

# rule: Classes implementing Serializable should declare an explicit private static final long serialVersionUID to avoid silent deserialization incompatibilities.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "serial-version-uid-required"


def _simple(name):
    return name.split(".")[-1].split("<")[0].strip()


def _implements_serializable(cls, src):
    intf = cls.child_by_field_name("interfaces")
    if intf is None:
        return False
    names = set()
    for t in find(intf, "type_identifier"):
        names.add(node_text(t, src).strip())
    for t in find(intf, "scoped_type_identifier"):
        names.add(_simple(node_text(t, src)))
    return "Serializable" in names


def _has_serial_uid(cls, src):
    body = cls.child_by_field_name("body")
    if body is None:
        return False
    for f in body.named_children:
        if f.type != "field_declaration":
            continue
        type_node = f.child_by_field_name("type")
        if type_node is None or node_text(type_node, src).strip() != "long":
            continue
        mods = [c for c in f.children if c.type == "modifiers"]
        mod_text = node_text(mods[0], src) if mods else ""
        if not ("private" in mod_text and "static" in mod_text and "final" in mod_text):
            continue
        for d in find(f, "variable_declarator"):
            name = d.child_by_field_name("name")
            if name is not None and node_text(name, src).strip() == "serialVersionUID":
                return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        if not _implements_serializable(cls, src_bytes):
            continue
        if _has_serial_uid(cls, src_bytes):
            continue
        name_node = cls.child_by_field_name("name")
        anchor = name_node if name_node is not None else cls
        line, col, _, _ = span(anchor)
        cls_label = (
            node_text(name_node, src_bytes) if name_node is not None else "<anon>"
        )
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": (
                    "Class '%s' implements Serializable but declares no "
                    "private static final long serialVersionUID." % cls_label
                ),
                "note": node_text(
                    cls.child_by_field_name("interfaces"), src_bytes
                ).strip(),
                "help": (
                    "Declare 'private static final long serialVersionUID = <value>L;' so "
                    "the serialized form stays compatible across class changes."
                ),
            }
        )
    return findings

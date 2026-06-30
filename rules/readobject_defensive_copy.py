# rule: readObject of a serializable class with private mutable fields must defensively copy them and validate invariants, or use a serialization proxy.
# (authored by RuleSmith from the description above)

# rule: readObject of a serializable class with private mutable fields must defensively copy them and validate invariants, or use a serialization proxy.
"""Flag readObject that fails to defensively copy private mutable fields (or use a serialization proxy)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "readobject-defensive-copy"

MUTABLE_HINTS = (
    "Date",
    "Calendar",
    "List",
    "Map",
    "Set",
    "Collection",
    "ArrayList",
    "HashMap",
    "HashSet",
    "LinkedList",
    "TreeMap",
    "TreeSet",
    "StringBuilder",
)


def _is_serializable(cls, src_b):
    for sup in find(cls, "super_interfaces"):
        if "Serializable" in node_text(sup, src_b):
            return True
    return False


def _method_names(cls, src_b):
    names = set()
    for m in find(cls, "method_declaration"):
        nm = m.child_by_field_name("name")
        if nm is not None:
            names.add(node_text(nm, src_b))
    return names


def _readobject(cls, src_b):
    for m in find(cls, "method_declaration"):
        nm = m.child_by_field_name("name")
        if nm is not None and node_text(nm, src_b) == "readObject":
            return m
    return None


def _private_mutable_fields(cls, src_b):
    out = {}
    for fld in find(cls, "field_declaration"):
        txt = node_text(fld, src_b)
        if "private" not in txt or "static" in txt:
            continue
        type_node = fld.child_by_field_name("type")
        if type_node is None:
            continue
        ttext = node_text(type_node, src_b)
        is_array = "[" in ttext
        is_mutable = is_array or any(h in ttext for h in MUTABLE_HINTS)
        if not is_mutable:
            continue
        for vd in find(fld, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                out[node_text(nm, src_b)] = span(fld)
    return out


def _copied_fields(method, src_b):
    copied = set()
    for asg in find(method, "assignment_expression"):
        left = asg.child_by_field_name("left")
        right = asg.child_by_field_name("right")
        if left is None or right is None:
            continue
        fname = node_text(left, src_b).split(".")[-1].strip()
        by_new = bool(find(right, "object_creation_expression"))
        by_clone = any(
            mi.child_by_field_name("name") is not None
            and node_text(mi.child_by_field_name("name"), src_b) == "clone"
            for mi in find(right, "method_invocation")
        )
        if by_new or by_clone:
            copied.add(fname)
    return copied


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        if not _is_serializable(cls, src_b):
            continue
        ro = _readobject(cls, src_b)
        if ro is None:
            continue
        names = _method_names(cls, src_b)
        if "writeReplace" in names and "readResolve" in names:
            continue  # serialization proxy in use
        fields = _private_mutable_fields(cls, src_b)
        if not fields:
            continue
        copied = _copied_fields(ro, src_b)
        missing = [f for f in fields if f not in copied]
        if not missing:
            continue
        cname_node = cls.child_by_field_name("name")
        cname = node_text(cname_node, src_b) if cname_node is not None else "?"
        line, col, _, _ = span(ro)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": (
                    f"readObject in serializable class '{cname}' does not defensively "
                    f"copy private mutable field(s): {', '.join(missing)}"
                ),
                "note": (
                    f"mutable state reachable from the deserialized stream and never "
                    f"copied: {', '.join(missing)}"
                ),
                "help": (
                    "Reassign each mutable field with a defensive copy "
                    "(this.f = new T(f) or f.clone()) and validate invariants inside "
                    "readObject, or replace readObject with a serialization proxy "
                    "(writeReplace + static proxy with readResolve)."
                ),
            }
        )
    return findings

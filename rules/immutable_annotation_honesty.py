# rule: A class annotated @Immutable that holds a non-final field, references a mutable collection/array, or leaks one via a getter is not actually immutable.
# (authored by RuleSmith from the description above)

# rule: A class annotated @Immutable that holds a non-final field, references a mutable collection/array, or leaks one via a getter is not actually immutable.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "immutable-annotation-honesty"

# Collection/array element types whose *contents* stay mutable even when the
# holding field is final, so a field of one of these breaks immutability.
MUTABLE_COLLECTION_TYPES = {
    "List",
    "Set",
    "Map",
    "Collection",
    "Queue",
    "Deque",
    "ArrayList",
    "LinkedList",
    "HashSet",
    "LinkedHashSet",
    "TreeSet",
    "HashMap",
    "LinkedHashMap",
    "TreeMap",
    "Vector",
    "Stack",
    "SortedSet",
    "SortedMap",
    "NavigableSet",
    "NavigableMap",
    "EnumSet",
    "EnumMap",
    "ConcurrentMap",
    "ConcurrentHashMap",
}


def _modifiers(node):
    return next((c for c in node.children if c.type == "modifiers"), None)


def _is_immutable_annotated(cls, sb):
    mods = _modifiers(cls)
    if mods is None:
        return False
    for ann in find(mods, "marker_annotation", "annotation"):
        name = ann.child_by_field_name("name")
        if name is not None and node_text(name, sb).split(".")[-1] == "Immutable":
            return True
    return False


def _is_mutable_collection_type(rtype, sb):
    if rtype is None:
        return False
    if rtype.type == "array_type":
        return True
    if rtype.type == "generic_type":
        base = rtype.named_children[0] if rtype.named_children else None
        return (
            base is not None
            and node_text(base, sb).split(".")[-1] in MUTABLE_COLLECTION_TYPES
        )
    if rtype.type in ("type_identifier", "scoped_type_identifier"):
        return node_text(rtype, sb).split(".")[-1] in MUTABLE_COLLECTION_TYPES
    return False


def _returned_field_name(ret, sb):
    """Field name returned directly by `return x;` / `return this.x;`, else None."""
    exprs = [c for c in ret.named_children]
    if not exprs:
        return None
    e = exprs[0]
    if e.type == "identifier":
        return node_text(e, sb)
    if e.type == "field_access":
        obj = e.child_by_field_name("object")
        fld = e.child_by_field_name("field")
        if obj is not None and obj.type == "this" and fld is not None:
            return node_text(fld, sb)
    return None


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        if not _is_immutable_annotated(cls, sb):
            continue
        body = cls.child_by_field_name("body")
        if body is None:
            continue

        collection_fields = set()  # field names of collection/array type
        for decl in [c for c in body.children if c.type == "field_declaration"]:
            mods = _modifiers(decl)
            modtext = node_text(mods, sb).split() if mods is not None else []
            if "static" in modtext:
                continue
            ftype = decl.child_by_field_name("type")
            is_collection = _is_mutable_collection_type(ftype, sb)
            for vd in find(decl, "variable_declarator"):
                name_node = vd.child_by_field_name("name")
                if name_node is None:
                    continue
                fname = node_text(name_node, sb)
                ln, c, *_ = span(name_node)
                if "final" not in modtext:
                    findings.append(
                        {
                            "rule": RULE,
                            "file": file,
                            "line": ln,
                            "col": c,
                            "message": f"@Immutable class has non-final field '{fname}'.",
                            "note": node_text(decl, sb).strip(),
                            "help": "Make every field final; a non-final field can be reassigned, so the object is not immutable.",
                        }
                    )
                elif is_collection:
                    collection_fields.add(fname)
                    findings.append(
                        {
                            "rule": RULE,
                            "file": file,
                            "line": ln,
                            "col": c,
                            "message": f"@Immutable class holds a mutable collection/array field '{fname}'.",
                            "note": node_text(decl, sb).strip(),
                            "help": "A final reference to a List/Map/Set/array is still mutable; wrap it in an unmodifiable view or use an immutable collection.",
                        }
                    )

        # getter leak: a method returning a collection/array field by reference
        for m in find(body, "method_declaration"):
            for ret in find(m, "return_statement"):
                fname = _returned_field_name(ret, sb)
                if fname is not None and fname in collection_fields:
                    ln, c, *_ = span(ret)
                    findings.append(
                        {
                            "rule": RULE,
                            "file": file,
                            "line": ln,
                            "col": c,
                            "message": f"@Immutable class leaks mutable field '{fname}' via a getter.",
                            "note": node_text(ret, sb).strip(),
                            "help": "Return a defensive copy or an unmodifiable view so callers cannot mutate internal state.",
                        }
                    )
    return findings

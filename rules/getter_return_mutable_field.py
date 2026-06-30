# rule: A getter/accessor must not return a direct reference to an internal mutable field (array, collection, Date); return a copy or unmodifiable view.
# (authored by RuleSmith from the description above)

# rule: A getter/accessor must not return a direct reference to an internal mutable field (array, collection, Date); return a copy or unmodifiable view.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "getter-return-mutable-field"

COLLECTION_TYPES = {
    "List",
    "Set",
    "Map",
    "Collection",
    "Iterable",
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
MUTABLE_SCALARS = {"Date", "Calendar"}


def _is_mutable_type(t, src):
    if t is None:
        return False
    if t.type == "array_type":
        return True
    if t.type == "generic_type":
        base = t.named_children[0] if t.named_children else None
        return (
            base is not None and node_text(base, src).split(".")[-1] in COLLECTION_TYPES
        )
    if t.type in ("type_identifier", "scoped_type_identifier"):
        name = node_text(t, src).split(".")[-1]
        return name in COLLECTION_TYPES or name in MUTABLE_SCALARS
    return False


def _mutable_fields(root, src):
    names = set()
    for fd in find(root, "field_declaration"):
        if not _is_mutable_type(fd.child_by_field_name("type"), src):
            continue
        for vd in find(fd, "variable_declarator"):
            n = vd.child_by_field_name("name")
            if n is not None:
                names.add(node_text(n, src))
    return names


def _returned_field_name(ret, src, fields):
    expr = next((c for c in ret.named_children), None)
    if expr is None:
        return None
    if expr.type == "identifier":
        name = node_text(expr, src)
    elif expr.type == "field_access":
        obj = expr.child_by_field_name("object")
        fld = expr.child_by_field_name("field")
        if obj is None or fld is None or obj.type != "this":
            return None
        name = node_text(fld, src)
    else:
        return None
    return name if name in fields else None


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    fields = _mutable_fields(tree.root_node, sb)
    findings = []
    if not fields:
        return findings
    for m in find(tree.root_node, "method_declaration"):
        if not _is_mutable_type(m.child_by_field_name("type"), sb):
            continue
        # locals/params shadowing a field name are not the internal field
        local = set()
        for p in find(m, "formal_parameter", "spread_parameter"):
            n = p.child_by_field_name("name")
            if n is not None:
                local.add(node_text(n, sb))
        for vd in find(m, "variable_declarator"):
            n = vd.child_by_field_name("name")
            if n is not None:
                local.add(node_text(n, sb))
        for ret in find(m, "return_statement"):
            name = _returned_field_name(ret, sb, fields)
            if name is None or name in local:
                continue
            line, col = span(ret)[0], span(ret)[1]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Getter returns a direct reference to an internal mutable field.",
                    "note": node_text(ret, sb).strip(),
                    "help": "Return a defensive copy (new ArrayList<>(f), Arrays.copyOf, new Date(d.getTime())) or an unmodifiable view (Collections.unmodifiableList).",
                }
            )
    return findings

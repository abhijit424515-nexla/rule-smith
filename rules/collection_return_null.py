# rule: Methods declared to return a collection or array should return an empty one rather than null to avoid caller NPEs.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "collection-return-null"

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


def _returns_collection_or_array(rtype, src):
    if rtype is None:
        return False
    if rtype.type == "array_type":
        return True
    if rtype.type == "generic_type":
        base = rtype.named_children[0] if rtype.named_children else None
        if base is None:
            return False
        return node_text(base, src).split(".")[-1] in COLLECTION_TYPES
    if rtype.type in ("type_identifier", "scoped_type_identifier"):
        return node_text(rtype, src).split(".")[-1] in COLLECTION_TYPES
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        rtype = m.child_by_field_name("type")
        if not _returns_collection_or_array(rtype, sb):
            continue
        # ponytail: a return inside a nested lambda/anon class is attributed to the
        # outer method here; rare for collection-returning methods, so skip the CFG.
        for ret in find(m, "return_statement"):
            null_node = None
            for ch in ret.named_children:
                if ch.type == "null_literal":
                    null_node = ch
                    break
            if null_node is None:
                continue
            line, col = span(null_node)[0], span(null_node)[1]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Method declared to return a collection/array returns null.",
                    "note": node_text(ret, sb).strip(),
                    "help": "Return an empty collection/array (Collections.emptyList(), List.of(), new int[0]) instead of null to avoid caller NPEs.",
                }
            )
    return findings

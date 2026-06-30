# rule: A public static final array or mutable collection constant is effectively mutable and lets callers alter shared state.
# (authored by RuleSmith from the description above)

# rule: A public static final array or mutable collection constant is effectively mutable and lets callers alter shared state.
"""Flag public static final fields whose declared type is an array or a mutable collection."""

from rulesmith.parse import parse, find, span, node_text

RULE = "public-static-final-mutable"

MUTABLE = {
    "List",
    "ArrayList",
    "LinkedList",
    "Vector",
    "Stack",
    "Set",
    "HashSet",
    "TreeSet",
    "LinkedHashSet",
    "Map",
    "HashMap",
    "TreeMap",
    "LinkedHashMap",
    "Hashtable",
    "Collection",
    "Queue",
    "Deque",
    "ArrayDeque",
    "PriorityQueue",
}


def _base_name(type_text):
    t = type_text.split("<")[0].strip()
    return t.split(".")[-1].rstrip("[]").strip()


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for fd in find(tree.root_node, "field_declaration"):
        mods = ""
        for ch in fd.children:
            if ch.type == "modifiers":
                mods = node_text(ch, src_b)
                break
        if not ("public" in mods and "static" in mods and "final" in mods):
            continue
        tnode = fd.child_by_field_name("type")
        if tnode is None:
            continue
        is_array = tnode.type == "array_type"
        base = _base_name(node_text(tnode, src_b))
        is_coll = base in MUTABLE
        if not (is_array or is_coll):
            continue
        line, col = span(fd)[0], span(fd)[1]
        kind = "array" if is_array else "mutable collection"
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"public static final {kind} constant is effectively mutable; callers can alter shared state",
                "note": f"declared type: {node_text(tnode, src_b)}",
                "help": "expose an immutable copy (List.copyOf / Collections.unmodifiable*) or a defensive accessor instead of the raw field",
            }
        )
    return findings

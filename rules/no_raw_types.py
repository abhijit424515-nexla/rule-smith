# rule: Generic types must be parameterized; raw types (List, Map, Set without type arguments) defeat compile-time type safety.
# (authored by RuleSmith from the description above)

# rule: Generic types must be parameterized; raw types (List, Map, Set without type arguments) defeat compile-time type safety.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "no-raw-types"

# JDK generic types whose raw use defeats type safety.
GENERIC_TYPES = {
    "List",
    "ArrayList",
    "LinkedList",
    "Vector",
    "Stack",
    "Map",
    "HashMap",
    "TreeMap",
    "LinkedHashMap",
    "Hashtable",
    "Set",
    "HashSet",
    "TreeSet",
    "LinkedHashSet",
    "Collection",
    "Queue",
    "Deque",
    "ArrayDeque",
    "Iterator",
    "Iterable",
    "Enumeration",
    "Optional",
    "Comparator",
    "Comparable",
    "Callable",
    "Future",
}


def _simple_name(node, src_bytes):
    return node_text(node, src_bytes).strip().split(".")[-1]


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = {}

    for node in find(tree.root_node, "type_identifier", "scoped_type_identifier"):
        parent = node.parent
        # parts of a scoped name (java / util / List) are not the type itself
        if (
            node.type == "type_identifier"
            and parent is not None
            and parent.type == "scoped_type_identifier"
        ):
            continue
        # base of a parameterized type (List in List<String>) is fine
        if parent is not None and parent.type == "generic_type":
            continue
        name = _simple_name(node, src_bytes)
        if name not in GENERIC_TYPES:
            continue
        line, col, _, _ = span(node)
        if line in findings:
            continue
        findings[line] = {
            "rule": RULE,
            "file": file,
            "line": line,
            "col": col,
            "message": "Raw type '%s'; parameterize it with type arguments." % name,
            "note": node_text(
                parent if parent is not None else node, src_bytes
            ).strip()[:120],
            "help": "Use %s<...> (e.g. %s<String>) so the compiler can enforce element types instead of falling back to Object."
            % (name, name),
        }

    return list(findings.values())

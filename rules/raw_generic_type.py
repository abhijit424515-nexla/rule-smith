# rule: Generic types must be parameterized; raw types (List, Map, Set without type arguments) defeat compile-time type safety.
# (authored by RuleSmith from the description above)

# rule: Generic types must be parameterized; raw types (List, Map, Set without type arguments) defeat compile-time type safety.
# (authored by RuleSmith from the description above)

"""Rule: raw-generic-type (detective).

Flags uses of generic collection types written without type arguments
(raw types): ``List x``, ``Map m``, ``new HashSet()``. A parameterized
use parses as a ``generic_type`` node (``List<String>``); a raw use is a
bare ``type_identifier`` sitting directly in a type position. We also skip
``scoped_type_identifier`` (e.g. ``Map.Entry``), where the name is a
qualifier rather than a raw type. Fix: add type arguments (``List<T>``,
``Map<K,V>``) or a diamond (``new HashSet<>()``).
"""

from rulesmith.parse import parse, find, node_text, span

RULE = "raw-generic-type"

# Generic JDK types that should always carry type arguments.
GENERIC_TYPES = {
    "List",
    "Map",
    "Set",
    "Collection",
    "Iterator",
    "Iterable",
    "Queue",
    "Deque",
    "ArrayList",
    "LinkedList",
    "HashMap",
    "LinkedHashMap",
    "TreeMap",
    "HashSet",
    "LinkedHashSet",
    "TreeSet",
    "Optional",
    "Comparable",
    "Comparator",
    "Class",
    "Future",
    "Callable",
}

# Parents where the name is parameterized or merely a qualifier, not raw.
_SKIP_PARENTS = {"generic_type", "scoped_type_identifier"}


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    seen = set()
    for node in find(tree.root_node, "type_identifier"):
        name = node_text(node, src_b)
        if name not in GENERIC_TYPES:
            continue
        if node.parent is not None and node.parent.type in _SKIP_PARENTS:
            continue
        line, col, _, _ = span(node)
        if (line, col) in seen:
            continue
        seen.add((line, col))
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Raw type '{name}' used without type arguments.",
                "note": node_text(node, src_b),
                "help": f"Parameterize it, e.g. '{name}<...>' (or a diamond "
                f"'new {name}<>()' for instantiation).",
            }
        )
    return findings

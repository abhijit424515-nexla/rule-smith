# rule: Flag a field storing data trivially derivable from another field (e.g. itemCount alongside the list), which creates a representable inconsistent state that can drift.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "redundant-derivable-field"

# Container fields whose contents make a count/size trivially derivable.
COLLECTION_TYPES = {
    "List",
    "ArrayList",
    "LinkedList",
    "Set",
    "HashSet",
    "TreeSet",
    "LinkedHashSet",
    "Map",
    "HashMap",
    "TreeMap",
    "LinkedHashMap",
    "Collection",
    "Queue",
    "Deque",
    "ArrayDeque",
    "Stack",
    "Vector",
}
# Numeric types a redundant count/size would use.
NUMERIC_TYPES = {"int", "long", "short", "Integer", "Long", "Short"}
# Name fragments that signal a value derivable from a container.
COUNT_HINTS = ("count", "size", "length", "num", "total")


def _type_name(type_node, sb):
    t = type_node.type
    if t == "array_type":
        return "array"
    if t == "generic_type":
        for ch in type_node.named_children:
            return node_text(ch, sb)
    return node_text(type_node, sb)


def _fields(class_node):
    body = class_node.child_by_field_name("body")
    if body is None:
        return []
    return [c for c in body.named_children if c.type == "field_declaration"]


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        fields = _fields(cls)
        # Does this class hold a container whose size is derivable?
        container = None
        for fd in fields:
            tn = fd.child_by_field_name("type")
            if tn is None:
                continue
            name = _type_name(tn, sb)
            if name in COLLECTION_TYPES or name == "array":
                vd = next(
                    (c for c in fd.named_children if c.type == "variable_declarator"),
                    None,
                )
                if vd is not None:
                    nn = vd.child_by_field_name("name")
                    container = node_text(nn, sb) if nn else "<container>"
                break
        if container is None:
            continue
        # Flag any numeric field whose name reads like that container's count.
        for fd in fields:
            tn = fd.child_by_field_name("type")
            if tn is None or _type_name(tn, sb) not in NUMERIC_TYPES:
                continue
            for vd in fd.named_children:
                if vd.type != "variable_declarator":
                    continue
                nn = vd.child_by_field_name("name")
                if nn is None:
                    continue
                fname = node_text(nn, sb)
                low = fname.lower()
                if any(h in low for h in COUNT_HINTS):
                    line, col, _el, _ec = span(nn)
                    findings.append(
                        {
                            "rule": RULE,
                            "file": file,
                            "line": line,
                            "col": col,
                            "message": (
                                "Field '%s' duplicates data derivable from container "
                                "'%s'; this is a representable inconsistent state."
                                % (fname, container)
                            ),
                            "note": (
                                "numeric field '%s' alongside container '%s' in same class"
                                % (fname, container)
                            ),
                            "help": (
                                "Drop the cached field and expose %s.size() (or length) "
                                "so the two cannot drift apart." % container
                            ),
                        }
                    )
    return findings

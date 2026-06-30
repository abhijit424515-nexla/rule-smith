# rule: A method that mutates a caller-supplied reference/collection parameter to return data hides a command inside its signature instead of using the return value.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "mutating-output-parameter"

# Caller-supplied container/reference types that callees tend to mutate as a
# hidden "out" channel instead of returning data.
_CONTAINER_HINTS = (
    "List",
    "Set",
    "Map",
    "Collection",
    "Iterable",
    "Queue",
    "Deque",
    "StringBuilder",
    "StringBuffer",
)

# Method names that clearly mutate the receiver container.
MUTATORS = {
    "add",
    "addAll",
    "remove",
    "removeAll",
    "removeIf",
    "retainAll",
    "put",
    "putAll",
    "putIfAbsent",
    "merge",
    "clear",
    "append",
    "insert",
    "set",
    "setLength",
    "push",
    "addFirst",
    "addLast",
    "offer",
    "replaceAll",
}


def _container_params(method, src):
    """[(name, param_node)] for params whose type looks like a mutable container."""
    out = []
    for fp in find(method, "formal_parameter", "spread_parameter"):
        t = fp.child_by_field_name("type")
        n = fp.child_by_field_name("name")
        if t is None or n is None:
            continue
        ttext = node_text(t, src)
        is_array = "[" in ttext
        is_container = any(h in ttext for h in _CONTAINER_HINTS)
        if is_array or is_container:
            out.append((node_text(n, src), fp))
    return out


def _mutating_calls_on(method, name, src):
    """method_invocation nodes that call a mutator on the bare param `name`."""
    hits = []
    for mi in find(method, "method_invocation"):
        obj = mi.child_by_field_name("object")
        nm = mi.child_by_field_name("name")
        if obj is None or nm is None:
            continue
        if obj.type != "identifier" or node_text(obj, src) != name:
            continue
        if node_text(nm, src) in MUTATORS:
            hits.append(mi)
    return hits


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration"):
        for name, pnode in _container_params(method, src_b):
            calls = _mutating_calls_on(method, name, src_b)
            if not calls:
                continue
            mi = calls[0]
            line, col, _, _ = span(pnode)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": (
                        "Method mutates caller-supplied parameter '%s' as a hidden "
                        "output channel instead of returning the data." % name
                    ),
                    "note": node_text(mi, src_b).strip()[:200],
                    "help": (
                        "Build a new collection locally and return it, so the side "
                        "effect is visible in the signature."
                    ),
                }
            )
    return findings

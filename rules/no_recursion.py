# rule: Functions must not call themselves directly or through a cycle in the call graph, keeping stack depth bounded.
# (authored by RuleSmith from the description above)

# rule: Functions must not call themselves directly or through a cycle in the call graph, keeping stack depth bounded.
"""Flag methods that recurse directly or via a cycle in the intra-class call graph."""

from rulesmith.parse import parse, find, span, node_text

RULE = "no-recursion"


def _name(node, src_b):
    n = node.child_by_field_name("name")
    return node_text(n, src_b) if n is not None else None


def _reaches_self(graph, start):
    seen = set()
    stack = list(graph.get(start, ()))
    while stack:
        n = stack.pop()
        if n == start:
            return True
        if n in seen:
            continue
        seen.add(n)
        stack.extend(graph.get(n, ()))
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    methods = find(tree.root_node, "method_declaration")
    names = {m for m in (_name(x, src_b) for x in methods) if m}

    # call graph over method names; only count self/this-qualified calls as internal
    graph = {n: set() for n in names}
    for m in methods:
        caller = _name(m, src_b)
        if not caller:
            continue
        for inv in find(m, "method_invocation"):
            obj = inv.child_by_field_name("object")
            if obj is not None and node_text(obj, src_b) != "this":
                continue
            callee = _name(inv, src_b)
            if callee in names:
                graph[caller].add(callee)

    findings = []
    for m in methods:
        name = _name(m, src_b)
        if not name or not _reaches_self(graph, name):
            continue
        nm = m.child_by_field_name("name")
        line, col, _, _ = span(nm if nm is not None else m)
        direct = name in graph.get(name, ())
        kind = "directly" if direct else "through a call-graph cycle"
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"method '{name}' recurses {kind}; stack depth is unbounded",
                "note": f"call graph edges from '{name}': {sorted(graph.get(name, ()))}",
                "help": "rewrite with an explicit work-list/stack or an iterative loop to bound stack depth",
            }
        )
    return findings

# rule: Flag explicit System.gc() / Runtime.getRuntime().gc() calls, which harm performance and rarely help.
# (authored by RuleSmith from the description above)

# rule: Flag explicit System.gc() / Runtime.getRuntime().gc() calls, which harm performance and rarely help.
"""Flag explicit System.gc() / Runtime.getRuntime().gc() calls."""

from rulesmith.parse import parse, find, span, node_text

RULE = "explicit-gc-call"


def _is_gc_target(obj, src_b):
    """True if `obj` is `System` or a `Runtime.getRuntime()` invocation."""
    if obj is None:
        return False
    if obj.type == "identifier" and node_text(obj, src_b) == "System":
        return True
    # Runtime.getRuntime().gc() -> object is itself a method_invocation getRuntime()
    if obj.type == "method_invocation":
        name = obj.child_by_field_name("name")
        if name is not None and node_text(name, src_b) == "getRuntime":
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for call in find(tree.root_node, "method_invocation"):
        name = call.child_by_field_name("name")
        if name is None or node_text(name, src_b) != "gc":
            continue
        obj = call.child_by_field_name("object")
        if not _is_gc_target(obj, src_b):
            continue
        line, col, _, _ = span(call)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "explicit garbage-collection request",
                "note": node_text(call, src_b),
                "help": "remove the call; the JVM manages GC, and forcing it stalls the application without reliably reclaiming more memory",
            }
        )
    return findings

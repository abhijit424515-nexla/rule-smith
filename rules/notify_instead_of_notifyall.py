# rule: notify() wakes a single arbitrary waiter and can strand others; prefer notifyAll() when multiple threads may wait on the monitor for different conditions.
# (authored by RuleSmith from the description above)

# rule: notify() wakes a single arbitrary waiter and can strand others; prefer notifyAll() when multiple threads may wait on the monitor for different conditions.
"""Flag monitor notify() calls; prefer notifyAll() so every waiter re-checks its condition."""

from rulesmith.parse import parse, find, span, node_text

RULE = "notify-instead-of-notifyall"


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for call in find(tree.root_node, "method_invocation"):
        name = call.child_by_field_name("name")
        if name is None or node_text(name, src_b) != "notify":
            continue
        # Object.notify() is nullary; an arg means it is an unrelated overload (observer-style).
        args = call.child_by_field_name("arguments")
        if args is not None and node_text(args, src_b).strip() not in ("", "()"):
            continue
        # Only implicit-this or this.notify() is the monitor protocol; foo.notify()
        # on some other receiver is almost always an unrelated API call.
        obj = call.child_by_field_name("object")
        if obj is not None and node_text(obj, src_b) != "this":
            continue
        line, col = span(call)[0], span(call)[1]
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "notify() wakes one arbitrary waiter and can strand others; use notifyAll()",
                "note": node_text(call, src_b),
                "help": "Replace notify() with notifyAll() so every waiting thread re-checks its condition.",
                "judge": True,
            }
        )
    return findings

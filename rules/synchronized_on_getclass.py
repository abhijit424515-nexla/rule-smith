# rule: synchronized(getClass()) locks the runtime class, so a subclass synchronizes on a different monitor than intended; use the explicit class literal.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "synchronized-on-getclass"

# rule: synchronized(getClass()) locks the runtime class, so a subclass synchronizes on a different monitor than intended; use the explicit class literal.


def _is_getclass_lock(mi, src_bytes):
    name = mi.child_by_field_name("name")
    if name is None or node_text(name, src_bytes) != "getClass":
        return False
    args = mi.child_by_field_name("arguments")
    if args is not None and node_text(args, src_bytes).replace(" ", "") != "()":
        return False
    obj = mi.child_by_field_name("object")
    # implicit this (no object) or explicit this.getClass()
    return obj is None or node_text(obj, src_bytes) == "this"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for sync in find(tree.root_node, "synchronized_statement"):
        lock = None
        for c in sync.children:
            if c.type == "parenthesized_expression":
                lock = c
                break
        if lock is None:
            continue
        # the lock expression must be the getClass() call
        for mi in find(lock, "method_invocation"):
            if _is_getclass_lock(mi, src_bytes):
                line, col, _, _ = span(mi)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "synchronized on getClass() locks the runtime class monitor",
                        "note": node_text(sync, src_bytes).splitlines()[0],
                        "help": "lock on the explicit class literal, e.g. synchronized(MyClass.class)",
                    }
                )
                break
    return findings

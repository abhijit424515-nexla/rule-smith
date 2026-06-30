# rule: Calling an overridable/external method, callback, or a blocking/long-running operation (I/O, sleep, join, future.get) while holding a lock risks deadlock and degrades liveness; use an open call.
# (authored by RuleSmith from the description above)

# rule: Calling an overridable/external method, callback, or a blocking/long-running operation (I/O, sleep, join, future.get) while holding a lock risks deadlock and degrades liveness; use an open call.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "blocking-call-while-holding-lock"

# ponytail: "holding a lock" ceiling = an enclosing synchronized(...) block or a
# synchronized method. ReentrantLock lock()/unlock() pairing left out (needs CFG
# region tracking). Blocking ops matched by a curated name set + Future.get via
# declared local type, not by general escape analysis. Upgrade both if needed.

BLOCKING_NAMES = {"sleep", "join", "await", "acquire", "take", "put"}


def _is_synchronized_method(m, sb):
    for c in m.children:
        if c.type == "modifiers":
            return "synchronized" in node_text(c, sb).split()
    return False


def _enclosing_sync(node):
    cur = node.parent
    while cur is not None:
        if cur.type == "synchronized_statement":
            return cur
        cur = cur.parent
    return None


def _future_vars(body, sb):
    names = set()
    for ld in find(body, "local_variable_declaration"):
        t = ld.child_by_field_name("type")
        if t is None or "Future" not in node_text(t, sb):
            continue
        for vd in find(ld, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                names.add(node_text(nm, sb))
    return names


def _blocking_reason(inv, sb, futures):
    nm = inv.child_by_field_name("name")
    if nm is None:
        return None
    name = node_text(nm, sb)
    obj = inv.child_by_field_name("object")
    otext = node_text(obj, sb) if obj is not None else ""
    if name in BLOCKING_NAMES:
        return "%s%s()" % (otext + "." if otext else "", name)
    if name == "get" and otext in futures:
        return "%s.get() blocks until the Future completes" % otext
    return None


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    root = tree.root_node
    findings = []
    for m in find(root, "method_declaration", "constructor_declaration"):
        body = m.child_by_field_name("body")
        if body is None:
            continue
        sync_method = _is_synchronized_method(m, sb)
        futures = _future_vars(body, sb)
        for inv in find(body, "method_invocation"):
            reason = _blocking_reason(inv, sb, futures)
            if reason is None:
                continue
            sync = _enclosing_sync(inv)
            if sync is None and not sync_method:
                continue
            where = (
                "inside a synchronized block"
                if sync is not None
                else "in synchronized method"
            )
            ln, col = span(inv)[0], span(inv)[1]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": ln,
                    "col": col,
                    "message": "Blocking/long-running call %s while holding a lock."
                    % reason,
                    "note": "%s is invoked %s, holding the monitor while it blocks."
                    % (reason, where),
                    "help": "Move the call outside the locked region (open call): release the lock, "
                    "or copy needed state under the lock and run the blocking work after.",
                }
            )
    return findings

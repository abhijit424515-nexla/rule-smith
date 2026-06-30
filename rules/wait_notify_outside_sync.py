# rule: Calling wait/notify/notifyAll on an object outside a synchronized block on that same object throws IllegalMonitorStateException at runtime.
# (authored by RuleSmith from the description above)

# rule: Calling wait/notify/notifyAll on an object outside a synchronized block on that same object throws IllegalMonitorStateException at runtime.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "wait-notify-outside-sync"

MONITOR = {"wait", "notify", "notifyAll"}

# ponytail: matches Object.wait/notify/notifyAll by name + receiver. Lock-held
# ceiling = an enclosing synchronized(target) block, or a synchronized instance
# method when target is "this". Upgrade if monitor is acquired via Lock objects.


def _is_synchronized_instance_method(m, sb):
    mods = None
    for c in m.children:
        if c.type == "modifiers":
            mods = node_text(c, sb).split()
            break
    if mods is None:
        return False
    return "synchronized" in mods and "static" not in mods


def _held(node, sb, target):
    cur = node.parent
    while cur is not None:
        if cur.type == "synchronized_statement":
            for ch in cur.children:
                if ch.type == "parenthesized_expression":
                    lock = node_text(ch, sb).strip()[1:-1].strip()
                    if lock == target:
                        return True
        cur = cur.parent
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    root = tree.root_node
    findings = []
    for m in find(root, "method_declaration"):
        body = m.child_by_field_name("body")
        if body is None:
            continue
        sync_method = _is_synchronized_instance_method(m, sb)
        for inv in find(body, "method_invocation"):
            nm = inv.child_by_field_name("name")
            if nm is None or node_text(nm, sb) not in MONITOR:
                continue
            obj = inv.child_by_field_name("object")
            target = "this" if obj is None else node_text(obj, sb)
            if _held(inv, sb, target):
                continue
            if target == "this" and sync_method:
                continue
            ln, col = span(inv)[0], span(inv)[1]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": ln,
                    "col": col,
                    "message": "%s() called on '%s' without holding its monitor."
                    % (node_text(nm, sb), target),
                    "note": "Call is not inside synchronized(%s){...}%s; runtime throws IllegalMonitorStateException."
                    % (
                        target,
                        " or a synchronized instance method"
                        if target == "this"
                        else "",
                    ),
                    "help": "Wrap the call in synchronized(%s){...} (or make the method synchronized when the receiver is 'this')."
                    % target,
                }
            )
    return findings

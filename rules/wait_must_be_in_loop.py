# rule: Object.wait() and Condition.await() must be called inside a loop that rechecks the predicate, to handle spurious wakeups and stale conditions.
# (authored by RuleSmith from the description above)

# rule: Object.wait() and Condition.await() must be called inside a loop that rechecks the predicate, to handle spurious wakeups and stale conditions.

from rulesmith.parse import parse, find, span, node_text

RULE = "wait-must-be-in-loop"

WAIT_NAMES = {"wait", "await", "awaitUninterruptibly", "awaitNanos", "awaitUntil"}
LOOP_TYPES = {
    "while_statement",
    "do_statement",
    "for_statement",
    "enhanced_for_statement",
}
# ponytail: flags monitor/condition waits not lexically enclosed by a loop.
# Matches by method name (wait/await*), not full type resolution -- upgrade to
# type inference if unrelated wait()/await() methods cause false positives.


def _in_loop(node, method):
    p = node.parent
    while p is not None and p.id != method.id:
        if p.type in LOOP_TYPES:
            return True
        p = p.parent
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        for inv in find(method, "method_invocation"):
            name = inv.child_by_field_name("name")
            if name is None or node_text(name, src_bytes) not in WAIT_NAMES:
                continue
            if _in_loop(inv, method):
                continue
            line, col, _, _ = span(inv)
            call = node_text(inv, src_bytes)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": (
                        "wait/await called outside a loop; recheck the predicate "
                        "in a while loop to handle spurious wakeups"
                    ),
                    "note": call,
                    "help": (
                        "Wrap in 'while (!condition) { ... "
                        + node_text(name, src_bytes)
                        + "(); }' so the predicate is rechecked after every wakeup."
                    ),
                }
            )
    return findings

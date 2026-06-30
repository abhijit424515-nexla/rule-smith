# rule: Expressions inside assert/Preconditions must not mutate state, since assertions may be disabled at runtime and must not alter behavior.
# (authored by RuleSmith from the description above)

# rule: Expressions inside assert/Preconditions must not mutate state, since assertions may be disabled at runtime and must not alter behavior.
# (authored by RuleSmith from the description above)

"""Rule: assert-no-side-effects (detective).

Assertions can be disabled at runtime (java -ea off, or a Preconditions check
stripped in a build profile), so any expression evaluated inside an assert
statement or a Guava-style Preconditions/Verify check must be pure. Flag
state-mutating expressions found there: assignments (= += ...), pre/post
increment-decrement (++ --), and calls to clearly mutating methods
(add/remove/put/set.../clear/...). Pure reads (size, get, contains, equals)
are fine.
"""

from rulesmith.parse import parse, find, span, node_text

RULE = "assert-no-side-effects"

# Static check helpers whose argument expressions must stay pure.
CHECK_RECEIVERS = {"Preconditions", "Verify", "Assertions", "Assert"}

# Method names that clearly mutate the receiver / a collection.
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
    "clear",
    "append",
    "push",
    "pop",
    "poll",
    "offer",
    "delete",
    "insert",
    "replace",
    "increment",
    "decrement",
    "next",
    "getAndIncrement",
    "getAndDecrement",
    "incrementAndGet",
    "decrementAndGet",
    "getAndSet",
    "compareAndSet",
}


def _is_mutator_name(name):
    if name in MUTATORS:
        return True
    # setX(...) setters mutate; bare "set" (a Set ctor-ish) excluded.
    return name.startswith("set") and len(name) > 3 and name[3].isupper()


def _mutations(scope, src_b):
    """Mutating expressions anywhere under `scope`."""
    hits = []
    for n in find(scope, "assignment_expression", "update_expression"):
        hits.append(n)
    for mi in find(scope, "method_invocation"):
        nm = mi.child_by_field_name("name")
        if nm is not None and _is_mutator_name(node_text(nm, src_b)):
            hits.append(mi)
    return hits


def _finding(node, where, file, src_b):
    line, col, _, _ = span(node)
    return {
        "rule": RULE,
        "file": file,
        "line": line,
        "col": col,
        "message": (
            f"State-mutating expression inside {where}; assertions may be "
            f"disabled at runtime and must not change behavior."
        ),
        "note": node_text(node, src_b).strip(),
        "help": (
            "Compute and store the value before the check, then assert on the "
            "already-computed result so behavior is identical with checks off."
        ),
    }


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    seen = set()

    # assert <cond> [: <detail>];
    for a in find(tree.root_node, "assert_statement"):
        for m in _mutations(a, src_b):
            if m.id in seen:
                continue
            seen.add(m.id)
            findings.append(_finding(m, "an assert statement", file, src_b))

    # Preconditions.checkX(...) / Verify.verify(...) argument expressions.
    for mi in find(tree.root_node, "method_invocation"):
        obj = mi.child_by_field_name("object")
        if obj is None or obj.type != "identifier":
            continue
        if node_text(obj, src_b) not in CHECK_RECEIVERS:
            continue
        args = mi.child_by_field_name("arguments")
        if args is None:
            continue
        for m in _mutations(args, src_b):
            if m.id in seen:
                continue
            seen.add(m.id)
            findings.append(_finding(m, "a Preconditions/Verify check", file, src_b))

    return findings

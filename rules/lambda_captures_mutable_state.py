# rule: A lambda or closure that captures and mutates an outer mutable variable, array, or collection breaks referential transparency and races when run concurrently.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "lambda-captures-mutable-state"


# rule: A lambda or closure that captures and mutates an outer mutable variable,
# array, or collection breaks referential transparency and races when run
# concurrently.

# Mutating method names on a captured collection/map/deque.
_MUTATORS = {
    "add",
    "addAll",
    "addFirst",
    "addLast",
    "put",
    "putAll",
    "putIfAbsent",
    "remove",
    "removeAll",
    "removeIf",
    "retainAll",
    "clear",
    "set",
    "push",
    "pop",
    "offer",
    "poll",
    "replaceAll",
    "merge",
    "compute",
    "computeIfAbsent",
    "computeIfPresent",
}


def _param_names(lam, src):
    p = lam.child_by_field_name("parameters")
    names = set()
    if p is None:
        return names
    if p.type == "identifier":
        names.add(node_text(p, src))
        return names
    fps = find(p, "formal_parameter", "spread_parameter")
    if fps:
        for fp in fps:
            nm = fp.child_by_field_name("name")
            if nm is not None:
                names.add(node_text(nm, src))
        return names
    # inferred params: (a, b) -> ...
    for ch in p.children:
        if ch.type == "identifier":
            names.add(node_text(ch, src))
    return names


def _local_names(lam, src):
    """Names declared *inside* this lambda body (not captured)."""
    names = set()
    for decl in find(lam, "local_variable_declaration"):
        for vd in find(decl, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                names.add(node_text(nm, src))
    for fe in find(lam, "enhanced_for_statement"):
        nm = fe.child_by_field_name("name")
        if nm is not None:
            names.add(node_text(nm, src))
    return names


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    seen = set()

    for lam in find(tree.root_node, "lambda_expression"):
        local = _param_names(lam, sb) | _local_names(lam, sb)

        # 1) Captured array/element write:  arr[i] = ...   arr[i] += ...
        for asn in find(lam, "assignment_expression"):
            left = asn.child_by_field_name("left")
            if left is None or left.type != "array_access":
                continue
            arr = left.child_by_field_name("array")
            if arr is None or arr.type != "identifier":
                continue
            name = node_text(arr, sb)
            if name in local:
                continue
            line, col = span(asn)[0], span(asn)[1]
            key = (line, col)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Lambda mutates captured array '%s'." % name,
                    "note": node_text(asn, sb),
                    "help": "Don't mutate captured state from a lambda; return a "
                    "new value or collect results functionally.",
                }
            )

        # 2) Captured collection mutation:  coll.add(...), map.put(...), etc.
        for mi in find(lam, "method_invocation"):
            obj = mi.child_by_field_name("object")
            nm = mi.child_by_field_name("name")
            if obj is None or nm is None or obj.type != "identifier":
                continue
            if node_text(nm, sb) not in _MUTATORS:
                continue
            name = node_text(obj, sb)
            if name in local:
                continue
            line, col = span(mi)[0], span(mi)[1]
            key = (line, col)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Lambda mutates captured collection '%s' via %s()."
                    % (name, node_text(nm, sb)),
                    "note": node_text(mi, sb),
                    "help": "Don't mutate captured state from a lambda; build a new "
                    "collection (e.g. stream().collect(...)) instead.",
                }
            )

    return findings

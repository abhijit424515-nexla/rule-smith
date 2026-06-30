# rule: Side effects (mutation, IO, external list.add) inside a map/filter/flatMap lambda violate the stateless/non-interference contract; side effects belong in forEach.
# (authored by RuleSmith from the description above)

# rule: Side effects (mutation, IO, external list.add) inside a map/filter/flatMap
# lambda violate the stateless/non-interference contract; side effects belong in forEach.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "no-side-effect-in-map-filter"


# Stream ops whose lambdas must be pure (non-interfering, stateless).
_PURE_OPS = {
    "map",
    "mapToInt",
    "mapToLong",
    "mapToObj",
    "mapToDouble",
    "filter",
    "flatMap",
    "flatMapToInt",
    "flatMapToLong",
}

# Mutating method names (collection/map/builder mutation = side effect).
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
    "append",
}

# IO method names (println etc. are observable side effects).
_IO = {"println", "print", "printf", "write", "flush", "format"}


def _param_names(lam, src):
    p = lam.child_by_field_name("parameters")
    names = set()
    if p is None:
        return names
    if p.type == "identifier":
        names.add(node_text(p, src))
        return names
    for fp in find(p, "formal_parameter", "spread_parameter"):
        nm = fp.child_by_field_name("name")
        if nm is not None:
            names.add(node_text(nm, src))
    for ch in p.children:
        if ch.type == "identifier":
            names.add(node_text(ch, src))
    return names


def _local_names(lam, src):
    names = set()
    for decl in find(lam, "local_variable_declaration"):
        for vd in find(decl, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                names.add(node_text(nm, src))
    return names


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    seen = set()

    for call in find(tree.root_node, "method_invocation"):
        nm = call.child_by_field_name("name")
        if nm is None or node_text(nm, sb) not in _PURE_OPS:
            continue
        args = call.child_by_field_name("arguments")
        if args is None:
            continue
        op = node_text(nm, sb)
        for lam in find(args, "lambda_expression"):
            # only lambdas that are *direct* args of this op (not nested ones).
            # tree-sitter re-wraps nodes, so compare by id, not identity.
            if lam.parent is None or lam.parent.id != args.id:
                continue
            local = _param_names(lam, sb) | _local_names(lam, sb)

            for mi in find(lam, "method_invocation"):
                mname_n = mi.child_by_field_name("name")
                if mname_n is None:
                    continue
                mname = node_text(mname_n, sb)
                obj = mi.child_by_field_name("object")

                hit = note = None
                if mname in _IO:
                    hit, note = ("IO", node_text(mi, sb))
                elif mname in _MUTATORS and obj is not None:
                    # mutation of an external (captured) collection
                    root = obj
                    while root.type == "field_access":
                        root = root.child_by_field_name("object") or root
                        break
                    rname = node_text(root, sb) if root.type == "identifier" else None
                    if rname is None or rname not in local:
                        hit, note = ("mutation", node_text(mi, sb))

                if hit is None:
                    continue
                line, col = span(mi)[0], span(mi)[1]
                if (line, col) in seen:
                    continue
                seen.add((line, col))
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "%s side effect (%s) inside %s() lambda."
                        % (hit.capitalize(), mname, op),
                        "note": note,
                        "help": "Keep map/filter/flatMap lambdas pure; move side "
                        "effects into forEach (or collect results functionally).",
                    }
                )

    return findings

# rule: A function expected to be pure must not write to a parameter's mutable state (field set, collection add/clear/remove, array store), since the caller's argument is silently mutated.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "pure-fn-no-param-mutation"


# Names that signal the author intends a pure/query function.
_PURE_PREFIXES = (
    "get",
    "is",
    "has",
    "compute",
    "calc",
    "calculate",
    "sum",
    "count",
    "total",
    "to",
    "from",
    "format",
    "parse",
    "find",
    "select",
    "map",
)

# Receiver-mutating method names (collection / bean mutators).
_MUTATORS = {
    "add",
    "addAll",
    "addFirst",
    "addLast",
    "clear",
    "remove",
    "removeAll",
    "removeIf",
    "retainAll",
    "put",
    "putAll",
    "putIfAbsent",
    "set",
    "sort",
    "replaceAll",
    "push",
    "pop",
    "offer",
    "poll",
    "merge",
}


def _params(method, src):
    names = set()
    for fp in find(method, "formal_parameter", "spread_parameter"):
        n = fp.child_by_field_name("name")
        if n is not None:
            names.add(node_text(n, src))
    return names


def _is_param(node, params, src):
    return (
        node is not None
        and node.type == "identifier"
        and node_text(node, src) in params
    )


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration"):
        name_node = method.child_by_field_name("name")
        if name_node is None:
            continue
        mname = node_text(name_node, src_bytes)
        if not mname.startswith(_PURE_PREFIXES):
            continue
        params = _params(method, src_bytes)
        if not params:
            continue

        # field set / array store: param.field = ...  or  param[i] = ...
        for assign in find(method, "assignment_expression"):
            left = assign.child_by_field_name("left")
            if left is None:
                continue
            if left.type == "field_access":
                obj = left.child_by_field_name("object")
                kind = "field set"
            elif left.type == "array_access":
                obj = left.child_by_field_name("array")
                kind = "array store"
            else:
                continue
            if _is_param(obj, params, src_bytes):
                line, col = span(left)[:2]
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "pure-looking method '%s' mutates parameter via %s"
                        % (mname, kind),
                        "note": node_text(assign, src_bytes),
                        "help": "Do not write to a parameter's state; return a new value or rename the method to signal mutation.",
                    }
                )

        # collection / bean mutator call on a parameter receiver.
        for inv in find(method, "method_invocation"):
            obj = inv.child_by_field_name("object")
            callee = inv.child_by_field_name("name")
            if callee is None or not _is_param(obj, params, src_bytes):
                continue
            if node_text(callee, src_bytes) in _MUTATORS:
                line, col = span(inv)[:2]
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "pure-looking method '%s' mutates parameter via %s()"
                        % (mname, node_text(callee, src_bytes)),
                        "note": node_text(inv, src_bytes),
                        "help": "Do not mutate a parameter's collection/state; return a new value or rename the method to signal mutation.",
                    }
                )
    return findings

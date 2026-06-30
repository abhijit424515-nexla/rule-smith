# rule: Methods named as queries (get/is/has/should) must be side-effect free; flag those that write fields or call mutating methods.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "query-method-side-effect"

_QUERY_PREFIXES = ("get", "is", "has", "should")
# common mutator method names; calling one inside a query is a side effect
_MUTATORS = {
    "add",
    "addAll",
    "put",
    "putAll",
    "remove",
    "removeAll",
    "clear",
    "append",
    "push",
    "pop",
    "insert",
    "delete",
    "write",
    "flush",
    "increment",
    "decrement",
    "update",
    "save",
    "close",
    "open",
}


def _class_field_names(tree, sb):
    names = set()
    for fd in find(tree.root_node, "field_declaration"):
        for vd in find(fd, "variable_declarator"):
            n = vd.child_by_field_name("name")
            if n is not None:
                names.add(node_text(n, sb))
    return names


def _is_field_target(node, sb, fields):
    if node.type == "field_access":
        obj = node.child_by_field_name("object")
        if obj is not None and node_text(obj, sb) == "this":
            return True
        return obj is not None and obj.type in ("this", "field_access")
    if node.type == "identifier":
        return node_text(node, sb) in fields
    return False


def _is_query_name(name):
    for p in _QUERY_PREFIXES:
        if name == p:
            return True
        if name.startswith(p) and len(name) > len(p) and name[len(p)].isupper():
            return True
    return False


def _mutating_call(method, sb):
    hits = []
    for mi in find(method, "method_invocation"):
        n = mi.child_by_field_name("name")
        if n is None:
            continue
        nm = node_text(n, sb)
        if nm in _MUTATORS or (
            nm.startswith("set") and len(nm) > 3 and nm[3].isupper()
        ):
            hits.append(mi)
    return hits


def _field_writes(method, sb, fields):
    hits = []
    for a in find(method, "assignment_expression"):
        left = a.child_by_field_name("left")
        if left is not None and _is_field_target(left, sb, fields):
            hits.append(a)
    for u in find(method, "update_expression"):  # x++ / --x
        for ch in u.named_children:
            if _is_field_target(ch, sb, fields):
                hits.append(u)
                break
    return hits


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    fields = _class_field_names(tree, sb)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        name_node = m.child_by_field_name("name")
        if name_node is None:
            continue
        name = node_text(name_node, sb)
        if not _is_query_name(name):
            continue
        # ponytail: name-prefix + mutator-name/field-write heuristic; no call
        # graph or alias analysis. Catches the obvious offenders, not transitive.
        ev = _field_writes(m, sb, fields) + _mutating_call(m, sb)
        if not ev:
            continue
        bad = ev[0]
        line, col = span(bad)[0], span(bad)[1]
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Query method '%s' has a side effect (writes a field or calls a mutating method)."
                % name,
                "note": node_text(bad, sb).strip(),
                "help": "Keep get/is/has/should methods side-effect free; move mutation into a separate command method.",
            }
        )
    return findings

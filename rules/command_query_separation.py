# rule: A method should not both mutate observable state and return a non-void value; commands that change state should return void, queries should be side-effect free.
# (authored by RuleSmith from the description above)

# rule: A method should not both mutate observable state and return a non-void value; commands that change state should return void, queries should be side-effect free.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "command-query-separation"


def _class_field_names(tree, sb):
    names = set()
    for fd in find(tree.root_node, "field_declaration"):
        for vd in find(fd, "variable_declarator"):
            n = vd.child_by_field_name("name")
            if n is not None:
                names.add(node_text(n, sb))
    return names


def _is_field_target(node, sb, fields):
    # this.x  -> field_access with object `this`
    if node.type == "field_access":
        obj = node.child_by_field_name("object")
        if obj is not None and node_text(obj, sb) == "this":
            return True
        # this.a.b = ... : nested field access still touches a field
        return obj is not None and obj.type in ("this", "field_access")
    # bare identifier matching a declared field (could be a local; weaker signal)
    if node.type == "identifier":
        return node_text(node, sb) in fields
    return False


def _mutations(method, sb, fields):
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


def _returns_value(method):
    for ret in find(method, "return_statement"):
        if ret.named_child_count > 0:
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    fields = _class_field_names(tree, sb)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        rtype = m.child_by_field_name("type")
        if rtype is None or node_text(rtype, sb) == "void":
            continue
        if not _returns_value(m):
            continue
        # ponytail: identifier-in-fieldset can be a shadowing local; this.x and
        # update on a field are the strong signals. Heuristic, no alias analysis.
        muts = _mutations(m, sb, fields)
        if not muts:
            continue
        mut = muts[0]
        line, col = span(mut)[0], span(mut)[1]
        name = m.child_by_field_name("name")
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Method '%s' returns a value and also mutates observable state (command/query mixed)."
                % (node_text(name, sb) if name else "?"),
                "note": node_text(mut, sb).strip(),
                "help": "Split into a void command that changes state and a side-effect-free query that returns the value.",
            }
        )
    return findings

# rule: Flag map.containsKey(k) guarding map.get(k) with a fallback, which is Map.getOrDefault or computeIfAbsent.
# (authored by RuleSmith from the description above)

# rule: Flag map.containsKey(k) guarding map.get(k) with a fallback, which is Map.getOrDefault or computeIfAbsent.
"""manual-getordefault: containsKey guarding a get on the same key with a fallback -> Map.getOrDefault / computeIfAbsent."""

from rulesmith.parse import parse, find, span, node_text

RULE = "manual-getordefault"


def _unwrap(node):
    # peel parentheses and a leading `!` so `if (!m.containsKey(k))` is handled too
    while node is not None and node.type in (
        "parenthesized_expression",
        "unary_expression",
    ):
        inner = node.child_by_field_name("operand")
        if inner is None:
            inner = node.named_children[0] if node.named_children else None
        node = inner
    return node


def _call(node):
    # returns (object_text, name_text, [arg_texts]) for a method_invocation, else None
    if node is None or node.type != "method_invocation":
        return None
    obj = node.child_by_field_name("object")
    name = node.child_by_field_name("name")
    argl = node.child_by_field_name("arguments")
    if obj is None or name is None or argl is None:
        return None
    return obj, name, argl


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for iff in find(tree.root_node, "if_statement"):
        cond = _unwrap(iff.child_by_field_name("condition"))
        c = _call(cond)
        if c is None:
            continue
        obj, name, argl = c
        if node_text(name, src_b) != "containsKey":
            continue
        if len(argl.named_children) != 1:
            continue
        obj_t = node_text(obj, src_b)
        key_t = node_text(argl.named_children[0], src_b)

        hit = False
        for br in (
            iff.child_by_field_name("consequence"),
            iff.child_by_field_name("alternative"),
        ):
            if br is None:
                continue
            for mi in find(br, "method_invocation"):
                g = _call(mi)
                if g is None:
                    continue
                gobj, gname, gargl = g
                if node_text(gname, src_b) != "get":
                    continue
                if node_text(gobj, src_b) != obj_t:
                    continue
                if len(gargl.named_children) != 1:
                    continue
                if node_text(gargl.named_children[0], src_b) != key_t:
                    continue
                hit = True
                break
            if hit:
                break
        if not hit:
            continue

        line, col, _, _ = span(cond)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"`{obj_t}.containsKey({key_t})` guards `{obj_t}.get({key_t})` with a fallback",
                "note": f"two lookups on `{obj_t}` for one logical access (containsKey then get)",
                "help": "collapse to Map.getOrDefault(k, default) or Map.computeIfAbsent(k, ...)",
                "judge": True,
            }
        )
    return findings

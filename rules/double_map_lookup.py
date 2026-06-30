# rule: Flag repeated get/containsKey/put on the same map with the same key in one method, replaceable by a single computeIfAbsent/merge that hashes once.
# (authored by RuleSmith from the description above)

# rule: Flag repeated get/containsKey/put on the same map with the same key in one method, replaceable by a single computeIfAbsent/merge that hashes once.
"""Repeated map lookups (get/containsKey/put) on the same map+key in one method."""

from rulesmith.parse import parse, find, span, node_text

RULE = "double-map-lookup"

# Map methods that hash the key on each call.
_MAP_METHODS = {
    "get",
    "containsKey",
    "put",
    "getOrDefault",
    "remove",
    "putIfAbsent",
    "containsValue",
}
# containsValue does not take a key first-arg, drop it.
_MAP_METHODS.discard("containsValue")


def _first_arg_text(inv, src_b):
    args = inv.child_by_field_name("arguments")
    if args is None:
        return None
    for ch in args.named_children:
        return node_text(ch, src_b)
    return None


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    methods = find(tree.root_node, "method_declaration", "constructor_declaration")
    for m in methods:
        # group: (map_text, key_text) -> list of (line, col, method_name)
        groups = {}
        for inv in find(m, "method_invocation"):
            name_node = inv.child_by_field_name("name")
            obj_node = inv.child_by_field_name("object")
            if name_node is None or obj_node is None:
                continue
            mname = node_text(name_node, src_b)
            if mname not in _MAP_METHODS:
                continue
            key = _first_arg_text(inv, src_b)
            if key is None:
                continue
            map_text = node_text(obj_node, src_b)
            line, col, _, _ = span(inv)
            groups.setdefault((map_text, key), []).append((line, col, mname))
        for (map_text, key), hits in groups.items():
            if len(hits) < 2:
                continue
            hits.sort()
            line, col, _ = hits[0]
            calls = ", ".join(sorted({h[2] for h in hits}))
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"`{map_text}` is looked up {len(hits)} times with key `{key}` in one method",
                    "note": f"calls on ({map_text}, {key}): {calls} \u2014 each rehashes the key",
                    "help": "collapse into a single computeIfAbsent/merge/getOrDefault so the key hashes once",
                    "judge": True,
                }
            )
    return findings

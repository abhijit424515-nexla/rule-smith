# rule: The result of Map.get(k) must not be dereferenced without first establishing that k is a key (containsKey guard or @KeyFor), since get may return null.
# (authored by RuleSmith from the description above)

# rule: The result of Map.get(k) must not be dereferenced without first establishing that k is a key (containsKey guard or @KeyFor), since get may return null.
"""map-get-without-containskey-guard (detective, dominance-based).

`map.get(k)` may return null. Dereferencing that result -- directly
(`m.get(k).foo()`) or via a local it was assigned to -- is an NPE unless a
`m.containsKey(k)` guard dominates the deref (or the local was null-checked).
Reuses the same cfg + dominance primitives as resource-leak / optional-get.
Name-based (no type resolution) so findings are judge=True candidates.
"""

from rulesmith.parse import parse, find, span, node_text
from rulesmith.cfg import build_method, dominators, dominates

RULE = "map-get-without-containskey-guard"


def _is_get_call(mi, src_b):
    # `obj.get(k)` with exactly one argument -> (obj_text, key_text), else None
    obj = mi.child_by_field_name("object")
    nm = mi.child_by_field_name("name")
    argl = mi.child_by_field_name("arguments")
    if obj is None or nm is None or argl is None:
        return None
    if node_text(nm, src_b) != "get" or len(argl.named_children) != 1:
        return None
    return node_text(obj, src_b), node_text(argl.named_children[0], src_b)


def _is_deref_of(node):
    # is `node` the receiver being dereferenced by its parent? (m.get(k).x / .foo())
    p = node.parent
    if p is None:
        return False
    if p.type in ("method_invocation", "field_access"):
        o = p.child_by_field_name("object")
        # tree-sitter returns fresh Node wrappers, so compare by byte span
        return (
            o is not None
            and o.start_byte == node.start_byte
            and o.end_byte == node.end_byte
        )
    return False


def _cfg_node_containing(cfg, ts_target):
    best = None
    for n in cfg.nodes.values():
        if n.ts is None:
            continue
        if (
            n.ts.start_byte <= ts_target.start_byte
            and n.ts.end_byte >= ts_target.end_byte
        ):
            if best is None or (n.ts.end_byte - n.ts.start_byte) < (
                best.ts.end_byte - best.ts.start_byte
            ):
                best = n
    return best


def _containskey_guards(cfg, src_b, obj_t, key_t):
    # cfg node ids whose statement establishes `obj.containsKey(key)`
    ids = set()
    needle = f"{obj_t}.containsKey("
    for n in cfg.nodes.values():
        if n.ts is None:
            continue
        txt = n.ts.text.decode("utf8", "replace")
        if needle in txt and key_t in txt:
            ids.add(n.id)
    return ids


def analyze_method(method_ts, src_b, file="<src>"):
    cfg = build_method(method_ts, src_b)
    dom = dominators(cfg)
    findings = []

    def guarded_by_containskey(deref_node, obj_t, key_t):
        dn = _cfg_node_containing(cfg, deref_node)
        if dn is None:
            return False
        for gid in _containskey_guards(cfg, src_b, obj_t, key_t):
            if gid != dn.id and dominates(dom, gid, dn.id):
                return True
        return False

    for mi in find(method_ts, "method_invocation"):
        got = _is_get_call(mi, src_b)
        if got is None:
            continue
        obj_t, key_t = got

        # Case A: direct chained dereference of the get() result
        if _is_deref_of(mi):
            if not guarded_by_containskey(mi, obj_t, key_t):
                sl, sc, _, _ = span(mi)
                findings.append(_finding(file, sl, sc, obj_t, key_t))
            continue

        # Case B: assigned to a local, then that local is dereferenced
        decl = mi.parent
        if decl is None or decl.type != "variable_declarator":
            continue
        nm = decl.child_by_field_name("name")
        if nm is None:
            continue
        var = node_text(nm, src_b)
        for use in find(method_ts, "identifier"):
            if node_text(use, src_b) != var or not _is_deref_of(use):
                continue
            if guarded_by_containskey(use, obj_t, key_t) or _nullchecked(
                cfg, dom, src_b, var, use
            ):
                continue
            sl, sc, _, _ = span(use)
            findings.append(_finding(file, sl, sc, obj_t, key_t))

    return findings


def _nullchecked(cfg, dom, src_b, var, use_node):
    # a `var != null` / `var == null` test dominating the deref makes it safe
    dn = _cfg_node_containing(cfg, use_node)
    if dn is None:
        return False
    needles = (f"{var} != null", f"{var} == null", f"null != {var}", f"null == {var}")
    for n in cfg.nodes.values():
        if n.ts is None or n.id == dn.id:
            continue
        txt = n.ts.text.decode("utf8", "replace")
        if any(s in txt for s in needles) and dominates(dom, n.id, dn.id):
            return True
    return False


def _finding(file, line, col, obj_t, key_t):
    return dict(
        rule=RULE,
        file=file,
        line=line,
        col=col,
        message=f"`{obj_t}.get({key_t})` result dereferenced without a containsKey guard",
        note=f"no {obj_t}.containsKey({key_t}) dominates this deref; get() returns null for an absent key -> NPE",
        help=f"guard with if ({obj_t}.containsKey({key_t})), or use {obj_t}.getOrDefault(...) / null-check the result",
        judge=True,
    )


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        out += analyze_method(m, src_b, file)
    return out

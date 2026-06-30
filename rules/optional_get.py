"""Rule: optional-get-without-ispresent (detective, dominance-based).

Optional.get() must be dominated by a presence guard (isPresent()/isDefined()/
isEmpty()) on every path, else it throws NoSuchElementException. Reuses the
same cfg + dominance primitives as resource-leak -- the guard-dominates-use
pattern that generalizes to NPE, bounds checks, and typestate.
"""

from rulesmith.parse import parse, find, span, node_text
from rulesmith.cfg import build_method, dominators, dominates

RULE = "optional-get-without-ispresent"

_PRESENCE = ("isPresent(", "isDefined(", "isEmpty(")


def _optional_locals(method_ts, src_b):
    names = set()
    for lvd in find(method_ts, "local_variable_declaration"):
        ty = lvd.child_by_field_name("type")
        if ty is None:
            continue
        leaf = node_text(ty, src_b).split("<")[0].strip().split(".")[-1]
        if leaf in ("Optional", "Option"):
            for decl in find(lvd, "variable_declarator"):
                nm = decl.child_by_field_name("name")
                if nm is not None:
                    names.add(node_text(nm, src_b))
    return names


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


def analyze_method(method_ts, src_b, file="<src>"):
    optionals = _optional_locals(method_ts, src_b)
    if not optionals:
        return []
    cfg = build_method(method_ts, src_b)
    dom = dominators(cfg)
    findings = []
    for mi in find(method_ts, "method_invocation"):
        obj = mi.child_by_field_name("object")
        nm = mi.child_by_field_name("name")
        if obj is None or nm is None or obj.type != "identifier":
            continue
        var = node_text(obj, src_b)
        if var not in optionals or node_text(nm, src_b) != "get":
            continue
        get_node = _cfg_node_containing(cfg, mi)
        if get_node is None:
            continue
        # any presence-guard node that dominates this get?
        guarded = False
        needle = [var + "." + p for p in _PRESENCE]
        for n in cfg.nodes.values():
            if n.ts is None or n.id == get_node.id:
                continue
            txt = n.ts.text.decode("utf8", "replace")
            if any(g in txt for g in needle) and dominates(dom, n.id, get_node.id):
                guarded = True
                break
        if not guarded:
            sl, sc, _, _ = span(mi)
            findings.append(
                dict(
                    rule=RULE,
                    file=file,
                    line=sl,
                    col=sc,
                    message=f"`{var}.get()` is not guarded by a presence check",
                    note="no isPresent()/isDefined() guard dominates this get(); "
                    "throws NoSuchElementException when empty",
                    help=f"guard with if ({var}.isPresent()) or use {var}.map(...)/orElse(...)",
                )
            )
    return findings


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        out += analyze_method(m, src_b, file)
    return out

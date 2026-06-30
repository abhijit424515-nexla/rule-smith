# rule: A downcast (Java cast or Scala asInstanceOf) not dominated by an instanceof/isInstanceOf check on the same value is a partial operation that can throw ClassCastException.
# (authored by RuleSmith from the description above)

"""Rule: unchecked-downcast (detective, dominance-based).

A Java cast (or Scala asInstanceOf) to a reference type is a partial operation:
it throws ClassCastException unless the runtime type already matches. It is safe
only when an `instanceof`/`isInstanceOf` test on the SAME value dominates the
cast on every path.
"""

from rulesmith.parse import parse, find, span, node_text
from rulesmith.cfg import build_method, dominators, dominates

RULE = "unchecked-downcast"

# primitive/numeric casts are never ClassCastException risks -- skip them
_PRIM = {"integral_type", "floating_point_type", "boolean_type", "void_type"}


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
    cfg = build_method(method_ts, src_b)
    dom = dominators(cfg)
    findings = []
    for cast in find(method_ts, "cast_expression"):
        ty = cast.child_by_field_name("type")
        val = cast.child_by_field_name("value")
        if ty is None or val is None or ty.type in _PRIM:
            continue
        # only reason about simple values; complex exprs are out of scope
        if val.type != "identifier":
            continue
        var = node_text(val, src_b)
        cast_node = _cfg_node_containing(cfg, cast)
        if cast_node is None:
            continue
        needle = var + " instanceof "
        guarded = False
        for n in cfg.nodes.values():
            if n.ts is None or n.id == cast_node.id:
                continue
            txt = n.ts.text.decode("utf8", "replace")
            if needle in txt and dominates(dom, n.id, cast_node.id):
                guarded = True
                break
        if not guarded:
            sl, sc, _, _ = span(cast)
            tyname = node_text(ty, src_b)
            findings.append(
                dict(
                    rule=RULE,
                    file=file,
                    line=sl,
                    col=sc,
                    message=f"downcast `({tyname}) {var}` is not guarded by an instanceof check",
                    note=f"no `{var} instanceof` test dominates this cast; throws "
                    "ClassCastException when the runtime type differs",
                    help=f"guard with if ({var} instanceof {tyname}) before casting",
                )
            )
    return findings


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        out += analyze_method(m, src_b, file)
    return out

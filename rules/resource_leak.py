"""Rule: resource-leak (flagship, detective).

An AutoCloseable acquired into a local must be closed on every path. Composes
cfg + post-dominance + escape analysis:
  - try-with-resources       -> safe (auto-closed)
  - escapes the method       -> skip (ownership transferred)
  - no close() at all        -> leak
  - close() present but does NOT post-dominate the acquisition -> leak
    (an exception or early return bypasses it)
"""
from rulesmith.parse import parse, find, span, node_text
from rulesmith.cfg import build_method, postdominators, postdominates
from rulesmith.dataflow import escapes

RULE = "resource-leak"

# name-based heuristic (no type resolution in MVP)
_CLOSEABLE_SUFFIX = (
    "InputStream", "OutputStream", "Reader", "Writer", "Stream",
    "Connection", "Statement", "ResultSet", "Scanner", "Socket",
    "Channel", "Session",
)
_CLOSEABLE_EXACT = {"Closeable", "AutoCloseable"}


def _type_leaf(type_text):
    # strip package + generics: java.util.stream.Stream<X> -> Stream
    t = type_text.split("<")[0].strip()
    return t.split(".")[-1]


def _is_closeable(type_text):
    leaf = _type_leaf(type_text)
    return leaf in _CLOSEABLE_EXACT or leaf.endswith(_CLOSEABLE_SUFFIX)


def _twr_resource_names(method_ts):
    names = set()
    for twr in find(method_ts, "try_with_resources_statement"):
        for res in find(twr, "resource"):
            ident = next((c for c in res.children if c.type == "identifier"), None)
            if ident is not None:
                names.add(ident.text.decode("utf8", "replace"))
    return names


def _cfg_node_containing(cfg, ts_target):
    best = None
    for n in cfg.nodes.values():
        if n.ts is None:
            continue
        if n.ts.start_byte <= ts_target.start_byte and n.ts.end_byte >= ts_target.end_byte:
            if best is None or (n.ts.end_byte - n.ts.start_byte) < (best.ts.end_byte - best.ts.start_byte):
                best = n
    return best


def _close_calls(method_ts, var):
    out = []
    for mi in find(method_ts, "method_invocation"):
        obj = mi.child_by_field_name("object")
        nm = mi.child_by_field_name("name")
        if obj is not None and nm is not None \
                and obj.type == "identifier" \
                and obj.text.decode("utf8", "replace") == var \
                and nm.text.decode("utf8", "replace") == "close":
            out.append(mi)
    return out


def analyze_method(method_ts, src_b, file="<src>"):
    findings = []
    safe = _twr_resource_names(method_ts)
    cfg = None
    pdom = None
    for lvd in find(method_ts, "local_variable_declaration"):
        ty = lvd.child_by_field_name("type")
        if ty is None:
            continue
        type_text = node_text(ty, src_b)
        if not _is_closeable(type_text):
            continue
        for decl in find(lvd, "variable_declarator"):
            nm = decl.child_by_field_name("name")
            val = decl.child_by_field_name("value")
            if nm is None or val is None:        # no initializer = not acquired here
                continue
            var = node_text(nm, src_b)
            if var in safe:
                continue
            if escapes(method_ts, var):
                continue
            sl, sc, _, _ = span(lvd)
            closes = _close_calls(method_ts, var)
            if not closes:
                findings.append(dict(
                    rule=RULE, file=file, line=sl, col=sc, var=var,
                    message=f"`{var}` ({_type_leaf(type_text)}) is never closed",
                    note="no close() call found and the resource does not escape the method",
                    help=f"close it in a finally block, or use try-with-resources: "
                         f"try ({type_text} {var} = ...) {{ ... }}",
                ))
                continue
            # close() exists: must post-dominate the acquisition
            if cfg is None:
                cfg = build_method(method_ts, src_b)
                pdom = postdominators(cfg)
            acq_node = _cfg_node_containing(cfg, lvd)
            ok = False
            for c in closes:
                cn = _cfg_node_containing(cfg, c)
                if acq_node is not None and cn is not None \
                        and postdominates(pdom, cn.id, acq_node.id):
                    ok = True
                    break
            if not ok:
                findings.append(dict(
                    rule=RULE, file=file, line=sl, col=sc, var=var,
                    message=f"`{var}` ({_type_leaf(type_text)}) may not be closed on all paths",
                    note="close() does not post-dominate the acquisition; an exception "
                         "or early return bypasses it",
                    help=f"use try-with-resources: try ({type_text} {var} = ...) {{ ... }}",
                ))
    return findings


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        out += analyze_method(m, src_b, file)
    return out

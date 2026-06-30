# rule: Every Closeable/AutoCloseable (stream, JDBC Connection, Statement, ResultSet, or other type with a close() obligation) opened in a method must be closed on every execution path including exceptions, ideally via try-with-resources.
# (authored by RuleSmith from the description above)

# rule: Every Closeable/AutoCloseable opened in a method must be closed on every path including exceptions, ideally via try-with-resources.

from rulesmith.parse import parse, find, span, node_text
from rulesmith.cfg import build_method, postdominators, postdominates
from rulesmith.dataflow import escapes

RULE = "closeable-must-close"

_SUFFIX = (
    "InputStream",
    "OutputStream",
    "Reader",
    "Writer",
    "Stream",
    "Connection",
    "Statement",
    "ResultSet",
    "Scanner",
    "Socket",
    "Channel",
    "Session",
)
_EXACT = {"Closeable", "AutoCloseable"}


def _leaf(type_text):
    # strip package + generics: java.util.stream.Stream<X> -> Stream
    return type_text.split("<")[0].strip().split(".")[-1]


def _is_closeable(type_text):
    leaf = _leaf(type_text)
    return leaf in _EXACT or leaf.endswith(_SUFFIX)


def _twr_names(method_ts):
    names = set()
    for twr in find(method_ts, "try_with_resources_statement"):
        for res in find(twr, "resource"):
            ident = next((c for c in res.children if c.type == "identifier"), None)
            if ident is not None:
                names.add(ident.text.decode("utf8", "replace"))
    return names


def _node_containing(cfg, target):
    best = None
    for n in cfg.nodes.values():
        if n.ts is None:
            continue
        if n.ts.start_byte <= target.start_byte and n.ts.end_byte >= target.end_byte:
            if best is None or (n.ts.end_byte - n.ts.start_byte) < (
                best.ts.end_byte - best.ts.start_byte
            ):
                best = n
    return best


def _close_calls(method_ts, var):
    out = []
    for mi in find(method_ts, "method_invocation"):
        obj = mi.child_by_field_name("object")
        nm = mi.child_by_field_name("name")
        if (
            obj is not None
            and nm is not None
            and obj.type == "identifier"
            and obj.text.decode("utf8", "replace") == var
            and nm.text.decode("utf8", "replace") == "close"
        ):
            out.append(mi)
    return out


def _analyze_method(method_ts, src_b, file):
    findings = []
    safe = _twr_names(method_ts)
    cfg = pdom = None
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
            if nm is None or val is None:  # no initializer = not acquired here
                continue
            var = node_text(nm, src_b)
            if var in safe or escapes(method_ts, var):
                continue
            sl, sc, _, _ = span(lvd)
            closes = _close_calls(method_ts, var)
            if not closes:
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": sl,
                        "col": sc,
                        "message": f"`{var}` ({_leaf(type_text)}) is never closed.",
                        "note": "no close() call found and the resource does not escape the method",
                        "help": f"use try-with-resources: try ({type_text} {var} = ...) {{ ... }}",
                    }
                )
                continue
            # close() exists: it must post-dominate the acquisition (run on all paths)
            if cfg is None:
                cfg = build_method(method_ts, src_b)
                pdom = postdominators(cfg)
            acq = _node_containing(cfg, lvd)
            ok = any(
                acq is not None
                and (cn := _node_containing(cfg, c)) is not None
                and postdominates(pdom, cn.id, acq.id)
                for c in closes
            )
            if not ok:
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": sl,
                        "col": sc,
                        "message": f"`{var}` ({_leaf(type_text)}) may not be closed on all paths.",
                        "note": "close() does not post-dominate the acquisition; an exception or early return bypasses it",
                        "help": f"use try-with-resources: try ({type_text} {var} = ...) {{ ... }}",
                    }
                )
    return findings


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        out += _analyze_method(m, src_b, file)
    return out

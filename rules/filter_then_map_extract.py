# rule: Flag a Stream.filter immediately followed by a map that re-extracts the tested value or unwraps an Optional, which collapses to a single flatMap.
# (authored by RuleSmith from the description above)

# rule: Flag a Stream.filter immediately followed by a map that re-extracts the tested value or unwraps an Optional, which collapses to a single flatMap.
"""filter-then-map-extract: filter+map that re-extracts the tested value or unwraps an Optional collapses to one flatMap."""

import re
from rulesmith.parse import parse, find, span, node_text

RULE = "filter-then-map-extract"


def _single_param(params, src):
    if params is None:
        return None
    t = params.type
    if t == "identifier":
        return node_text(params, src)
    kids = list(params.named_children)
    if t == "inferred_parameters" and len(kids) == 1 and kids[0].type == "identifier":
        return node_text(kids[0], src)
    if (
        t == "formal_parameters"
        and len(kids) == 1
        and kids[0].type == "formal_parameter"
    ):
        name = kids[0].child_by_field_name("name")
        return node_text(name, src) if name else None
    return None


def _lambda(inv, src):
    args = inv.child_by_field_name("arguments")
    if args is None:
        return None
    lams = [c for c in args.named_children if c.type == "lambda_expression"]
    return lams[0] if lams else None


def _ret_expr(lam, src):
    body = lam.child_by_field_name("body")
    if body is None:
        return None
    if body.type == "block":
        rets = find(body, "return_statement")
        if not rets:
            return None
        kids = list(rets[0].named_children)
        return kids[0] if kids else None
    return body


def _norm(node, src, pname):
    if node is None:
        return ""
    txt = node_text(node, src)
    if pname:
        txt = re.sub(r"\b" + re.escape(pname) + r"\b", "_P_", txt)
    return re.sub(r"\s+", "", txt)


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    out = []
    for mi in find(tree.root_node, "method_invocation"):
        name = mi.child_by_field_name("name")
        if name is None or node_text(name, sb) != "map":
            continue
        obj = mi.child_by_field_name("object")
        if obj is None or obj.type != "method_invocation":
            continue
        oname = obj.child_by_field_name("name")
        if oname is None or node_text(oname, sb) != "filter":
            continue
        flam = _lambda(obj, sb)
        mlam = _lambda(mi, sb)
        if flam is None or mlam is None:
            continue
        fp = _single_param(flam.child_by_field_name("parameters"), sb)
        mp = _single_param(mlam.child_by_field_name("parameters"), sb)
        ftext = _norm(flam.child_by_field_name("body"), sb, fp)
        mtext = _norm(_ret_expr(mlam, sb), sb, mp)
        reason = None
        # Case A: filter checks Optional.isPresent(), map unwraps with get()
        if "isPresent()" in ftext and "_P_.get()" in mtext:
            reason = "filter tests isPresent() and map calls get() on the same value"
        # Case B: map re-extracts the same (non-trivial) expression the filter tests
        elif mtext and mtext != "_P_" and re.search(r"[.(]", mtext) and mtext in ftext:
            reason = "map re-extracts the same expression the filter tests"
        if reason is None:
            continue
        ln, col, *_ = span(mi)
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": ln,
                "col": col,
                "message": "filter+map that re-extracts or unwraps collapses to a single flatMap",
                "note": reason,
                "help": "Replace .filter(p).map(extract) with one .flatMap(...) (Optional::stream for the unwrap case).",
                "judge": True,
            }
        )
    return out

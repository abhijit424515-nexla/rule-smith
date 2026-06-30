# rule: Flag tainted input controlling the destination URL/host of an outbound HTTP client request (HttpClient, URL.openConnection).
# (authored by RuleSmith from the description above)

# rule: Flag tainted input controlling the destination URL/host of an outbound HTTP client request (HttpClient, URL.openConnection).
"""SSRF: user-controlled URL/host reaching an outbound HTTP request sink."""

from rulesmith.parse import parse, find, node_text, span

RULE = "ssrf-user-controlled-url"

# method names whose return value originates from untrusted input
TAINT_SOURCES = {
    "getParameter",
    "getParameterValues",
    "getHeader",
    "getHeaders",
    "getQueryString",
    "getRequestURI",
    "getRequestURL",
    "getCookies",
    "getInputStream",
    "getReader",
    "getPathInfo",
    "getPathTranslated",
    "nextLine",
    "readLine",
}
# Spring binding annotations that mark a parameter as request-controlled
TAINT_ANNOS = {
    "RequestParam",
    "PathVariable",
    "RequestHeader",
    "RequestBody",
    "CookieValue",
    "ModelAttribute",
}
# invocation names that take a destination URL/URI as their first argument
SINK_CALLS = {
    "uri",
    "getForObject",
    "getForEntity",
    "postForObject",
    "postForEntity",
    "exchange",
    "getForLocation",
    "openStream",
}


def _expr_tainted(node, tainted, src_b):
    if node is None:
        return False
    if node.type == "identifier" and node_text(node, src_b) in tainted:
        return True
    for mi in find(node, "method_invocation"):
        nm = mi.child_by_field_name("name")
        if nm is not None and node_text(nm, src_b) in TAINT_SOURCES:
            return True
    for idn in find(node, "identifier"):
        if node_text(idn, src_b) in tainted:
            return True
    return False


def _first_arg(args):
    if args is None:
        return None
    for c in args.named_children:
        return c
    return None


def _tainted_names(method_node, src_b):
    tainted = set()
    for p in find(method_node, "formal_parameter"):
        names = set()
        for a in find(p, "marker_annotation", "annotation"):
            an = a.child_by_field_name("name")
            if an is not None:
                names.add(node_text(an, src_b))
        if names & TAINT_ANNOS:
            pn = p.child_by_field_name("name")
            if pn is not None:
                tainted.add(node_text(pn, src_b))
    decls = find(method_node, "variable_declarator")
    asgs = find(method_node, "assignment_expression")
    changed = True
    while changed:
        changed = False
        for d in decls:
            nm = d.child_by_field_name("name")
            val = d.child_by_field_name("value")
            if nm is not None:
                name = node_text(nm, src_b)
                if name not in tainted and _expr_tainted(val, tainted, src_b):
                    tainted.add(name)
                    changed = True
        for a in asgs:
            left = a.child_by_field_name("left")
            right = a.child_by_field_name("right")
            if left is not None and left.type == "identifier":
                name = node_text(left, src_b)
                if name not in tainted and _expr_tainted(right, tainted, src_b):
                    tainted.add(name)
                    changed = True
    return tainted


def _sinks(method_node, src_b):
    out = []
    for oc in find(method_node, "object_creation_expression"):
        t = oc.child_by_field_name("type")
        tn = node_text(t, src_b) if t is not None else ""
        if tn in ("URL", "URI") or tn.startswith("Http"):
            arg = _first_arg(oc.child_by_field_name("arguments"))
            if arg is not None:
                out.append((oc, arg, "new " + tn))
    for mi in find(method_node, "method_invocation"):
        nm = mi.child_by_field_name("name")
        nmt = node_text(nm, src_b) if nm is not None else ""
        if nmt == "create":
            obj = mi.child_by_field_name("object")
            if obj is None or node_text(obj, src_b) not in ("URI", "URL"):
                continue
            arg = _first_arg(mi.child_by_field_name("arguments"))
            if arg is not None:
                out.append((mi, arg, "URI.create"))
        elif nmt in SINK_CALLS:
            arg = _first_arg(mi.child_by_field_name("arguments"))
            if arg is not None:
                out.append((mi, arg, nmt))
    return out


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    seen = set()
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        tainted = _tainted_names(m, src_b)
        if not tainted:
            continue
        for sink_node, arg, label in _sinks(m, src_b):
            if not _expr_tainted(arg, tainted, src_b):
                continue
            line, col, _, _ = span(sink_node)
            if line in seen:
                continue
            seen.add(line)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Tainted input controls the destination of an outbound HTTP request (SSRF).",
                    "note": "sink `%s` receives `%s`, derived from untrusted input"
                    % (label, node_text(arg, src_b)),
                    "help": "Validate the host against an allowlist of permitted destinations before issuing the request.",
                    "judge": True,
                }
            )
    return findings

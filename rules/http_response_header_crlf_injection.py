# rule: Flag tainted input written into response headers/cookies enabling CRLF response splitting.
# (authored by RuleSmith from the description above)

# rule: Flag tainted input written into response headers/cookies enabling CRLF response splitting.
"""HTTP response header CRLF injection: tainted input flowing into response header/cookie sinks (response splitting)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "http-response-header-crlf-injection"

# Response header / cookie sinks by method name.
SINKS = {"setHeader", "addHeader", "addCookie", "addDateHeader"}

# Taint-source method names (servlet / IO / user input).
SOURCES = {
    "getParameter",
    "getParameterValues",
    "getHeader",
    "getHeaders",
    "getQueryString",
    "getInputStream",
    "getReader",
    "getCookies",
    "readLine",
    "nextLine",
    "getRequestURI",
    "getRequestURL",
    "getQueryParam",
    "getPathInfo",
    "getRemoteUser",
    "getValue",
}

# Sanitizers / encoders that strip CR/LF -> treat value as cleaned.
SANITIZERS = {
    "replace",
    "replaceAll",
    "replaceFirst",
    "encode",
    "encodeURIComponent",
    "escapeHttpHeader",
    "stripNewlines",
    "sanitize",
    "strip",
}


def _has_call(node, src_b, names):
    for call in find(node, "method_invocation"):
        nm = call.child_by_field_name("name")
        if nm is not None and node_text(nm, src_b) in names:
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        tainted = set()
        # locals assigned (directly or transitively) from a source call.
        for _ in range(2):  # small fixpoint for x = ... + tainted
            for decl in find(m, "local_variable_declaration"):
                for vd in find(decl, "variable_declarator"):
                    val = vd.child_by_field_name("value")
                    nm = vd.child_by_field_name("name")
                    if val is None or nm is None:
                        continue
                    if _has_call(val, src_b, SOURCES) or any(
                        node_text(i, src_b) in tainted for i in find(val, "identifier")
                    ):
                        tainted.add(node_text(nm, src_b))

        for call in find(m, "method_invocation"):
            nm = call.child_by_field_name("name")
            if nm is None or node_text(nm, src_b) not in SINKS:
                continue
            args = call.child_by_field_name("arguments")
            if args is None:
                continue
            # sanitized in place -> no CRLF can survive.
            if _has_call(args, src_b, SANITIZERS):
                continue
            tainted_arg = _has_call(args, src_b, SOURCES) or any(
                node_text(i, src_b) in tainted for i in find(args, "identifier")
            )
            if not tainted_arg:
                continue
            line, col, *_ = span(call)
            sink = node_text(nm, src_b)
            out.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"tainted input written to response sink '{sink}()' (CRLF response splitting)",
                    "note": node_text(call, src_b)[:200],
                    "help": 'strip CR/LF (e.g. value.replaceAll("[\\r\\n]", "")) or reject values containing line breaks',
                    "judge": True,
                }
            )
    return out

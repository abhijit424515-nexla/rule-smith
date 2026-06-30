# rule: Flag untrusted input passed to SpEL/OGNL/ScriptEngine/Velocity evaluation APIs, enabling remote code execution.
# (authored by RuleSmith from the description above)

# rule: Flag untrusted input passed to SpEL/OGNL/ScriptEngine/Velocity evaluation APIs, enabling remote code execution.
"""Expression-language injection: tainted input reaching SpEL/OGNL/ScriptEngine/Velocity eval sinks (possible RCE)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "expression-language-injection"

# Eval sinks by method name: SpEL/OGNL parseExpression, ScriptEngine eval,
# Velocity evaluate/mergeTemplate.
SINKS = {"eval", "parseExpression", "evaluate", "mergeTemplate"}

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
    "getQueryParam",
    "getBody",
}

# Param/var name substrings that imply untrusted input.
TAINT_NAMES = (
    "input",
    "request",
    "payload",
    "userdata",
    "username",
    "untrusted",
    "param",
    "query",
    "tainted",
)


def _has_source_call(node, src_b):
    for call in find(node, "method_invocation"):
        nm = call.child_by_field_name("name")
        if nm is not None and node_text(nm, src_b) in SOURCES:
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        tainted = set()
        # params with suspicious names
        params = m.child_by_field_name("parameters")
        if params is not None:
            for p in find(params, "formal_parameter", "spread_parameter"):
                nm = p.child_by_field_name("name")
                if nm is not None:
                    n = node_text(nm, src_b)
                    if any(t in n.lower() for t in TAINT_NAMES):
                        tainted.add(n)
        # locals assigned from a source call
        for decl in find(m, "local_variable_declaration"):
            for vd in find(decl, "variable_declarator"):
                val = vd.child_by_field_name("value")
                nm = vd.child_by_field_name("name")
                if val is not None and nm is not None and _has_source_call(val, src_b):
                    tainted.add(node_text(nm, src_b))

        for call in find(m, "method_invocation"):
            nm = call.child_by_field_name("name")
            if nm is None or node_text(nm, src_b) not in SINKS:
                continue
            args = call.child_by_field_name("arguments")
            if args is None:
                continue
            tainted_arg = _has_source_call(args, src_b)
            if not tainted_arg:
                for ident in find(args, "identifier"):
                    if node_text(ident, src_b) in tainted:
                        tainted_arg = True
                        break
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
                    "message": f"untrusted input passed to expression/script sink '{sink}()' (possible RCE)",
                    "note": node_text(call, src_b)[:200],
                    "help": "validate against an allowlist or evaluate only static, trusted expressions",
                    "judge": True,
                }
            )
    return out

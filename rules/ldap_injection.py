# rule: Flag DirContext.search/LdapTemplate filter strings assembled by concatenating tainted input without escaping LDAP special characters.
# (authored by RuleSmith from the description above)

# rule: Flag DirContext.search/LdapTemplate filter strings assembled by concatenating tainted input without escaping LDAP special characters.

from rulesmith.parse import parse, find, span, node_text

RULE = "ldap-injection"

# Methods that take an LDAP filter string (DirContext / LdapTemplate family).
SEARCH_METHODS = {"search", "searchForObject", "searchForContext"}

# Calls that produce attacker-controlled values.
TAINT_SOURCES = {
    "getParameter",
    "getParameterValues",
    "getParameterMap",
    "getParameterNames",
    "getHeader",
    "getHeaders",
    "getQueryString",
    "getRequestURI",
    "getRequestURL",
    "getCookies",
    "getInputStream",
    "getReader",
    "readLine",
    "nextLine",
    "getAttribute",
    "getProperty",
    "getenv",
}

# Escapers that neutralize LDAP filter metacharacters.
ESCAPERS = {
    "filterEncode",
    "encodeForLDAP",
    "encodeForDN",
    "escapeLDAPSearchFilter",
    "escapeDN",
    "escapeLdap",
}


def _is_escaped(node, src_b):
    # Climb to the nearest enclosing call; escaped iff that call is an LDAP escaper.
    n = node.parent
    while n is not None:
        if n.type == "method_invocation":
            mn = n.child_by_field_name("name")
            return bool(mn and node_text(mn, src_b) in ESCAPERS)
        n = n.parent
    return False


def _concat_taint(node, taint, src_b):
    # Return (unescaped tainted names, has LDAP-filter-shaped literal) for a concat.
    bad = []
    for ident in find(node, "identifier"):
        nm = node_text(ident, src_b)
        if nm in taint and not _is_escaped(ident, src_b):
            bad.append(nm)
    has_filter = any(
        ("(" in node_text(lit, src_b) or "=" in node_text(lit, src_b))
        for lit in find(node, "string_literal")
    )
    return bad, has_filter


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        taint = set()
        for p in find(method, "formal_parameter", "spread_parameter"):
            nm = p.child_by_field_name("name")
            if nm:
                taint.add(node_text(nm, src_b))
        # locals assigned directly from a taint source
        for decl in find(method, "local_variable_declaration"):
            for vd in find(decl, "variable_declarator"):
                nm = vd.child_by_field_name("name")
                val = vd.child_by_field_name("value")
                if nm and val and val.type == "method_invocation":
                    mn = val.child_by_field_name("name")
                    if mn and node_text(mn, src_b) in TAINT_SOURCES:
                        taint.add(node_text(nm, src_b))
        # filter vars built by concatenating tainted input (propagates taint)
        filter_concats = {}
        for decl in find(method, "local_variable_declaration"):
            for vd in find(decl, "variable_declarator"):
                nm = vd.child_by_field_name("name")
                val = vd.child_by_field_name("value")
                if nm and val and val.type == "binary_expression":
                    bad, has_filter = _concat_taint(val, taint, src_b)
                    if bad and has_filter:
                        name = node_text(nm, src_b)
                        filter_concats[name] = (val, bad)
                        taint.add(name)
        # report tainted, unescaped filters reaching a search call
        for call in find(method, "method_invocation"):
            mn = call.child_by_field_name("name")
            if not mn or node_text(mn, src_b) not in SEARCH_METHODS:
                continue
            args = call.child_by_field_name("arguments")
            if not args:
                continue
            for arg in args.named_children:
                concat = bad = None
                if arg.type == "binary_expression":
                    b, has_filter = _concat_taint(arg, taint, src_b)
                    if b and has_filter:
                        concat, bad = arg, b
                elif (
                    arg.type == "identifier" and node_text(arg, src_b) in filter_concats
                ):
                    concat, bad = filter_concats[node_text(arg, src_b)]
                if concat is None:
                    continue
                line, col, _, _ = span(mn)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"LDAP filter for {node_text(mn, src_b)}() built by concatenating "
                        f"unescaped tainted input ({', '.join(sorted(set(bad)))})",
                        "note": "filter: " + node_text(concat, src_b),
                        "help": "escape with LdapEncoder.filterEncode / ESAPI encodeForLDAP, "
                        "or use a parameterized filter with {0} placeholders",
                        "judge": True,
                    }
                )
    return findings

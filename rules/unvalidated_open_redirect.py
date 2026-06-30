# rule: Flag user-controlled input passed to HttpServletResponse.sendRedirect without an allowlist of destinations.
# (authored by RuleSmith from the description above)

# rule: Flag user-controlled input passed to HttpServletResponse.sendRedirect without an allowlist of destinations.
"""Open redirect: sendRedirect target derived from request input with no allowlist."""

from rulesmith.parse import parse, find, span, node_text

RULE = "unvalidated-open-redirect"

# Servlet request accessors that return attacker-controlled data.
_SOURCES = (
    "getParameter",
    "getParameterValues",
    "getParameterMap",
    "getHeader",
    "getHeaders",
    "getQueryString",
    "getRequestURI",
    "getRequestURL",
    "getPathInfo",
    "getCookies",
)


def _is_source_call(node, src_b):
    if node is None or node.type != "method_invocation":
        return False
    name = node.child_by_field_name("name")
    return name is not None and node_text(name, src_b) in _SOURCES


def _tainted_vars(tree, src_b):
    """Names of locals/assignments whose value is a source call or a copy of a tainted var."""
    tainted = set()

    def value_taints(val):
        if val is None:
            return False
        if _is_source_call(val, src_b):
            return True
        if val.type == "identifier":
            return node_text(val, src_b) in tainted
        if val.type in ("binary_expression", "parenthesized_expression"):
            return any(value_taints(c) for c in val.named_children)
        return False

    # fixpoint so `b = a` picks up a tainted `a` regardless of order
    changed = True
    while changed:
        changed = False
        for decl in find(tree.root_node, "local_variable_declaration"):
            for d in find(decl, "variable_declarator"):
                nnode = d.child_by_field_name("name")
                if nnode is None:
                    continue
                nm = node_text(nnode, src_b)
                if nm not in tainted and value_taints(d.child_by_field_name("value")):
                    tainted.add(nm)
                    changed = True
        for asn in find(tree.root_node, "assignment_expression"):
            lhs = asn.child_by_field_name("left")
            if lhs is None or lhs.type != "identifier":
                continue
            nm = node_text(lhs, src_b)
            if nm not in tainted and value_taints(asn.child_by_field_name("right")):
                tainted.add(nm)
                changed = True
    return tainted


def _arg_is_tainted(node, tainted, src_b):
    """True if the value reaching the sink is raw tainted data.
    A tainted value wrapped in another call (lookup/sanitizer/allowlist) is NOT flagged."""
    if node is None:
        return False
    if node.type == "method_invocation":
        # only a direct source call counts; do not descend into a wrapping call's args
        return _is_source_call(node, src_b)
    if node.type == "identifier":
        return node_text(node, src_b) in tainted
    if node.type in ("binary_expression", "parenthesized_expression"):
        return any(_arg_is_tainted(c, tainted, src_b) for c in node.named_children)
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    tainted = _tainted_vars(tree, src_b)
    out = []
    for inv in find(tree.root_node, "method_invocation"):
        name = inv.child_by_field_name("name")
        if name is None or node_text(name, src_b) != "sendRedirect":
            continue
        args = inv.child_by_field_name("arguments")
        if args is None:
            continue
        argvals = [c for c in args.named_children]
        if not argvals or not _arg_is_tainted(argvals[0], tainted, src_b):
            continue
        line, col, _, _ = span(inv)
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "sendRedirect() target is derived from request input with no destination allowlist",
                "note": f"tainted redirect: `{node_text(inv, src_b)}`",
                "help": "validate the destination against a fixed allowlist (or map a request key to a known internal path) before calling sendRedirect",
                "judge": True,
            }
        )
    return out

# rule: The isPresent()-then-get() if/else shape should be flagged and rewritten with map/orElse/ifPresentOrElse, since it reduces Optional to a glorified null check.
# (authored by RuleSmith from the description above)

# rule: The isPresent()-then-get() if/else shape should be flagged and rewritten with map/orElse/ifPresentOrElse, since it reduces Optional to a glorified null check.
"""isPresent()-then-get(): an if (x.isPresent()) { ... x.get() ... } shape
that should be a map/orElse/ifPresentOrElse combinator instead of a glorified
null check. Matches the guard variable in the condition against a .get() on the
same variable in the consequence."""

from rulesmith.parse import parse, find, span, node_text

RULE = "ispresent-get-should-use-combinator"


def _ispresent_var(node, src_b):
    """If `node` subtree contains `<id>.isPresent()`, return the id text."""
    for mi in find(node, "method_invocation"):
        nm = mi.child_by_field_name("name")
        obj = mi.child_by_field_name("object")
        if nm is None or obj is None or obj.type != "identifier":
            continue
        if node_text(nm, src_b) == "isPresent":
            return node_text(obj, src_b)
    return None


def _calls_get(node, src_b, var):
    """True if `node` subtree contains `var.get()`."""
    for mi in find(node, "method_invocation"):
        nm = mi.child_by_field_name("name")
        obj = mi.child_by_field_name("object")
        if nm is None or obj is None or obj.type != "identifier":
            continue
        if node_text(nm, src_b) == "get" and node_text(obj, src_b) == var:
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for iff in find(tree.root_node, "if_statement"):
        cond = iff.child_by_field_name("condition")
        cons = iff.child_by_field_name("consequence")
        if cond is None or cons is None:
            continue
        var = _ispresent_var(cond, src_b)
        if var is None or not _calls_get(cons, src_b, var):
            continue
        line, col, _, _ = span(iff)
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"`if ({var}.isPresent()) {{ ... {var}.get() ... }}` reduces Optional to a null check",
                "note": node_text(cond, src_b),
                "help": f"Rewrite with {var}.map(...).orElse(...) or {var}.ifPresentOrElse(...)",
            }
        )
    return out

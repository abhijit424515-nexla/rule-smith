# rule: toString, hashCode, equals, and finalize must not throw, as exceptions from them break callers, collections, and debuggers.
# (authored by RuleSmith from the description above)

# rule: toString, hashCode, equals, and finalize must not throw, as exceptions from them break callers, collections, and debuggers.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "throw-from-special-method"

# The four methods the JVM, collections, and debuggers call implicitly.
SPECIAL = {"toString", "hashCode", "equals", "finalize"}

# A throw inside a nested method / lambda / inner class belongs to THAT
# scope, not to the special method that lexically contains it.
_BOUNDARY = {
    "method_declaration",
    "constructor_declaration",
    "lambda_expression",
    "class_body",
}


def _owned_by(node, method):
    """True if `node` lives in `method`'s own body, not a nested scope."""
    cur = node.parent
    while cur is not None and cur.id != method.id:
        if cur.type in _BOUNDARY:
            return False
        cur = cur.parent
    return cur is not None and cur.id == method.id


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        nm = m.child_by_field_name("name")
        if nm is None:
            continue
        name = node_text(nm, src_bytes)
        if name not in SPECIAL:
            continue
        # A declared `throws` clause is a promise the method may throw.
        for thr in (c for c in m.children if c.type == "throws"):
            line, col, _, _ = span(thr)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"{name} declares a checked-exception 'throws' clause.",
                    "note": node_text(thr, src_bytes),
                    "help": f"{name} must not throw; handle the exception internally.",
                }
            )
        # Explicit throw statements in this method's own body.
        for t in find(m, "throw_statement"):
            if not _owned_by(t, m):
                continue
            line, col, _, _ = span(t)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"{name} can throw; exceptions here break callers, collections, and debuggers.",
                    "note": node_text(t, src_bytes),
                    "help": f"{name} must not throw; return a safe value instead.",
                }
            )
    return findings

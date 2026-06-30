# rule: a non-abstract, non-empty-by-design method must not have an empty body

from rulesmith.parse import parse, find, span, node_text

RULE = "no-empty-method-body"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    # Only method_declaration: constructors are excluded (empty ctors are
    # routinely empty by design). Abstract/native/interface methods have no
    # block body, so child_by_field_name("body") is None and they self-skip.
    for m in find(tree.root_node, "method_declaration"):
        body = m.child_by_field_name("body")
        if body is None or body.type != "block":
            continue  # abstract / native / interface: no body to be empty
        named = body.named_children
        stmts = [c for c in named if c.type != "comment"]
        if stmts:
            continue  # has real code
        if any(c.type == "comment" for c in named):
            continue  # empty by design: a comment documents the intent
        name = m.child_by_field_name("name")
        nm = node_text(name, src_bytes) if name is not None else "<anon>"
        sl, sc, _, _ = span(m)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": sl,
                "col": sc,
                "message": f"Method '{nm}' has an empty body.",
                "note": node_text(m, src_bytes).splitlines()[0].strip(),
                "help": "Implement the method, make it abstract, or add a comment explaining why it is intentionally empty.",
            }
        )
    return findings

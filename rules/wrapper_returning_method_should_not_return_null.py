# rule: A method declared to return a boxed Boolean/Byte/Character (or other wrapper used in arithmetic or conditionals) must not return null, since auto-unboxing at the call site throws NPE.
# (authored by RuleSmith from the description above)

# rule: A method declared to return a boxed Boolean/Byte/Character (or other wrapper used in arithmetic or conditionals) must not return null, since auto-unboxing at the call site throws NPE.
"""Method declared to return a boxed wrapper must not return null (auto-unboxing NPEs the caller)."""

from rulesmith.parse import parse, find, node_text, span

RULE = "wrapper-returning-method-should-not-return-null"
WRAPPERS = {
    "Boolean",
    "Byte",
    "Character",
    "Short",
    "Integer",
    "Long",
    "Float",
    "Double",
}


def analyze_source(src, file="<src>"):
    tree, b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration"):
        t = m.child_by_field_name("type")
        if t is None:
            continue
        rtype = node_text(t, b)
        if rtype not in WRAPPERS:
            continue
        for r in find(m, "return_statement"):
            # `return null;` has exactly one named child: the null_literal itself.
            # `return foo(null);` nests null_literal under a method_invocation, so it is skipped.
            if r.named_child_count == 1 and r.named_children[0].type == "null_literal":
                line, col, *_ = span(r)
                out.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"method returns boxed {rtype} but returns null; auto-unboxing at the call site throws NPE",
                        "note": f"return type {rtype} is a boxed primitive and `return null;` reaches the caller here",
                        "help": f"return a non-null {rtype}, or change the return type to a primitive or Optional<{rtype}>",
                    }
                )
    return out

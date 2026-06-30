# rule: Constructors taking many parameters (especially several of the same type) should be replaced by the Builder pattern.
# (authored by RuleSmith from the description above)

# rule: Constructors taking many parameters (especially several of the same type) should be replaced by the Builder pattern.
"""Flag telescoping constructors that should be replaced by the Builder pattern."""

from collections import Counter

from rulesmith.parse import parse, find, span, node_text

RULE = "telescoping-constructor-use-builder"

MANY_PARAMS = 5  # a constructor this wide is telescoping on its own
WIDE_ENOUGH = 4  # at this width, repeated param types alone justify a builder


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for ctor in find(tree.root_node, "constructor_declaration"):
        params_node = ctor.child_by_field_name("parameters")
        if params_node is None:
            continue
        params = [
            c
            for c in params_node.named_children
            if c.type in ("formal_parameter", "spread_parameter")
        ]
        n = len(params)
        types = []
        for p in params:
            t = p.child_by_field_name("type")
            if t is not None:
                types.append(node_text(t, src_b))
        max_dup = max(Counter(types).values()) if types else 0

        if n >= MANY_PARAMS:
            reason = f"{n} constructor parameters"
        elif n >= WIDE_ENOUGH and max_dup >= 2:
            reason = f"{n} parameters, {max_dup} of the same type"
        else:
            continue

        line, col, _, _ = span(ctor)
        name = ctor.child_by_field_name("name")
        cname = node_text(name, src_b) if name is not None else "<ctor>"
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"constructor '{cname}' has {reason}; use the Builder pattern",
                "note": reason
                + " (swapping same-typed args is silent and easy to miss)",
                "help": "replace the telescoping constructor with a Builder",
                "judge": True,
            }
        )
    return findings

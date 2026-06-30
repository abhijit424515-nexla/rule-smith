# rule: A method whose entire body forwards the same/near-same arguments to another method with no added value indicates a poor responsibility split.
# (authored by RuleSmith from the description above)

# rule: A method whose entire body forwards the same/near-same arguments to another method with no added value indicates a poor responsibility split.
"""Flag pass-through methods that only forward their parameters to another call."""

from rulesmith.parse import parse, find, span, node_text

RULE = "pass-through-method"


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        body = m.child_by_field_name("body")
        if body is None:
            continue
        # exactly one real statement in the body (ignore comments)
        stmts = [c for c in body.named_children if c.type != "comment"]
        if len(stmts) != 1:
            continue
        stmt = stmts[0]
        if stmt.type not in ("return_statement", "expression_statement"):
            continue
        inner_exprs = [c for c in stmt.named_children if c.type != "comment"]
        if not inner_exprs:
            continue
        inv = inner_exprs[0]
        if inv.type != "method_invocation":
            continue

        params = m.child_by_field_name("parameters")
        if params is None:
            continue
        param_names = [
            node_text(p.child_by_field_name("name"), src_b)
            for p in params.named_children
            if p.type == "formal_parameter" and p.child_by_field_name("name")
        ]
        if not param_names:
            continue

        arglist = inv.child_by_field_name("arguments")
        if arglist is None:
            continue
        args = list(arglist.named_children)
        if len(args) != len(param_names):
            continue
        # every argument must be a bare identifier matching the param in order
        if not all(
            a.type == "identifier" and node_text(a, src_b) == pn
            for a, pn in zip(args, param_names)
        ):
            continue

        inner = inv.child_by_field_name("name")
        inner_name = node_text(inner, src_b) if inner else "?"
        name_node = m.child_by_field_name("name")
        line, col, _, _ = span(name_node or m)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"method only forwards its parameters to {inner_name}(...)",
                "note": f"body is a single call forwarding ({', '.join(param_names)}) unchanged",
                "help": "inline the call at its sites or fold the missing logic in here; a pure pass-through is a layer with no value",
                "judge": True,
            }
        )
    return findings

# rule: Flag methods or constructors with two or more adjacent boolean parameters; encode the variant as an enum or sealed type to make invalid states unrepresentable.
# (authored by RuleSmith from the description above)

# rule: Flag methods or constructors with two or more adjacent boolean parameters; encode the variant as an enum or sealed type to make invalid states unrepresentable.
"""Two or more adjacent boolean parameters are boolean-blindness; model the variant as an enum/sealed type."""

from rulesmith.parse import parse, find, span, node_text

RULE = "boolean-blindness-multi-flag-params"

_BOOL_TYPES = {"boolean", "Boolean"}


def _params(method):
    plist = method.child_by_field_name("parameters")
    if plist is None:
        return []
    return [
        c for c in plist.children if c.type in ("formal_parameter", "spread_parameter")
    ]


def _is_bool(param, src_b):
    t = param.child_by_field_name("type")
    if t is None:
        return False
    return node_text(t, src_b) in _BOOL_TYPES


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        params = _params(method)
        flags = [_is_bool(p, src_b) for p in params]
        # longest run of adjacent booleans
        run = best = 0
        start = best_start = -1
        for i, f in enumerate(flags):
            if f:
                if run == 0:
                    start = i
                run += 1
                if run > best:
                    best, best_start = run, start
            else:
                run = 0
        if best < 2:
            continue
        name_node = method.child_by_field_name("name")
        anchor = name_node if name_node is not None else params[best_start]
        line, col, _, _ = span(anchor)
        mname = node_text(name_node, src_b) if name_node is not None else "<init>"
        bad = params[best_start : best_start + best]
        evidence = ", ".join(node_text(p, src_b) for p in bad)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"'{mname}' has {best} adjacent boolean parameters",
                "note": f"adjacent boolean run: {evidence}",
                "help": "encode the variant as an enum or sealed type so invalid combinations cannot be expressed",
            }
        )
    return findings

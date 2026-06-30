# rule: Flag a Stream.map/Optional.map/collection transform whose lambda returns its argument unchanged (x -> x), a no-op that should be removed.
# (authored by RuleSmith from the description above)

# rule: Flag a Stream.map/Optional.map/collection transform whose lambda returns its argument unchanged (x -> x), a no-op that should be removed.
"""Identity map operation: .map(x -> x) is a no-op; remove it."""

from rulesmith.parse import parse, find, span, node_text

RULE = "identity-map-operation"

_TRANSFORMS = {"map", "transform"}


def _lambda_params(lam, src_b):
    p = lam.child_by_field_name("parameters")
    if p is None:
        return []
    if p.type == "identifier":
        return [node_text(p, src_b)]
    names = []
    if p.type == "inferred_parameters":
        for c in p.named_children:
            if c.type == "identifier":
                names.append(node_text(c, src_b))
    elif p.type == "formal_parameters":
        for fp in p.named_children:
            n = fp.child_by_field_name("name")
            if n is not None:
                names.append(node_text(n, src_b))
    return names


def _is_identity(lam, src_b):
    params = _lambda_params(lam, src_b)
    if len(params) != 1:
        return False
    pname = params[0]
    body = lam.child_by_field_name("body")
    if body is None:
        return False
    if body.type == "identifier":
        return node_text(body, src_b) == pname
    if body.type == "block":
        stmts = list(body.named_children)
        if len(stmts) == 1 and stmts[0].type == "return_statement":
            exprs = list(stmts[0].named_children)
            if len(exprs) == 1 and exprs[0].type == "identifier":
                return node_text(exprs[0], src_b) == pname
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for mi in find(tree.root_node, "method_invocation"):
        name = mi.child_by_field_name("name")
        if name is None or node_text(name, src_b) not in _TRANSFORMS:
            continue
        args = mi.child_by_field_name("arguments")
        if args is None:
            continue
        for a in args.named_children:
            if a.type == "lambda_expression" and _is_identity(a, src_b):
                line, col, _, _ = span(a)
                out.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "map/transform with an identity lambda (x -> x) is a no-op",
                        "note": node_text(mi, src_b),
                        "help": "Remove the identity map call; it returns its input unchanged",
                    }
                )
    return out

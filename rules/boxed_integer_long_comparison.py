# rule: do not compare boxed Integer or Long values with == or !=, use equals

from rulesmith.parse import parse, find, span, node_text

RULE = "boxed-integer-long-comparison"


def analyze_source(src, file="<src>"):
    findings = []
    tree, src_bytes = parse(src)

    boxed_vars = {}
    for decl in find(tree.root_node, "local_variable_declaration"):
        type_text = None
        for child in decl.children:
            if child.type == "type_identifier":
                type_text = node_text(child, src_bytes)
                break

        if type_text in ("Integer", "Long"):
            for var_declarator in find(decl, "variable_declarator"):
                for child in var_declarator.children:
                    if child.type == "identifier":
                        var_name = node_text(child, src_bytes)
                        boxed_vars[var_name] = type_text
                        break

    for expr in find(tree.root_node, "binary_expression"):
        children = list(expr.children)
        if len(children) < 3:
            continue

        op_idx = None
        for i, child in enumerate(children):
            if child.type in ("==", "!="):
                op_idx = i
                break

        if op_idx is None or op_idx < 1 or op_idx >= len(children) - 1:
            continue

        left = children[op_idx - 1]
        right = children[op_idx + 1]
        op = children[op_idx]

        left_boxed = is_boxed_expr(left, src_bytes, boxed_vars)
        right_boxed = is_boxed_expr(right, src_bytes, boxed_vars)

        if left_boxed or right_boxed:
            line, col, _, _ = span(expr)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Boxed Integer or Long compared with == or !=; use equals() instead",
                    "note": f"{node_text(left, src_bytes)} {node_text(op, src_bytes)} {node_text(right, src_bytes)}",
                    "help": "Use .equals() for boxed type comparisons",
                }
            )

    return findings


def is_boxed_expr(expr, src_bytes, boxed_vars):
    if expr.type == "identifier":
        name = node_text(expr, src_bytes)
        return name in boxed_vars

    if expr.type == "method_invocation":
        identifiers = find(expr, "identifier")
        for ident in identifiers:
            name = node_text(ident, src_bytes)
            if name in (
                "valueOf",
                "parseInt",
                "parseLong",
                "decode",
                "getInteger",
                "getLong",
            ):
                return True

    if expr.type == "object_creation_expression":
        type_ids = find(expr, "type_identifier")
        if type_ids:
            name = node_text(type_ids[0], src_bytes)
            if name in ("Integer", "Long"):
                return True

    if expr.type == "cast_expression":
        type_ids = find(expr, "type_identifier")
        if type_ids:
            name = node_text(type_ids[0], src_bytes)
            if name in ("Integer", "Long"):
                return True

    return False

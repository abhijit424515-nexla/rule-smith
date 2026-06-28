from rulesmith.parse import parse, find, node_text, span

RULE = "string-equality-check"

def analyze_source(src, file="<src>") -> list:
    findings = []
    tree, src_bytes = parse(src)
    
    for binary_expr in find(tree.root_node, "binary_expression"):
        left = binary_expr.child_by_field_name("left")
        operator = binary_expr.child_by_field_name("operator")
        right = binary_expr.child_by_field_name("right")
        
        if not operator or not left or not right:
            continue
        
        op_text = node_text(operator, src_bytes)
        if op_text not in ("==", "!="):
            continue
        
        if left.type == "string_literal" or right.type == "string_literal":
            line, col, _, _ = span(binary_expr)
            expr_text = node_text(binary_expr, src_bytes)
            findings.append({
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Use .equals() to compare strings, not '{op_text}'",
                "note": expr_text,
                "help": "Replace '==' with .equals() for string comparison"
            })
    
    return findings
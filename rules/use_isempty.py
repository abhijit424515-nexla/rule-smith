# rule: use isEmpty() instead of comparing size() == 0 on a collection

from rulesmith.parse import parse, find, node_text

RULE = "use-isempty"


def _is_size_call(node, src):
    if node is None or node.type != "method_invocation":
        return False
    name = node.child_by_field_name("name")
    if name is None or node_text(name, src) != "size":
        return False
    args = node.child_by_field_name("arguments")
    # empty argument list -> no named children
    return args is not None and args.named_child_count == 0


def _is_zero(node, src):
    return node is not None and node_text(node, src).strip() == "0"


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for be in find(tree.root_node, "binary_expression"):
        op_node = be.child_by_field_name("operator")
        left = be.child_by_field_name("left")
        right = be.child_by_field_name("right")
        if op_node is None or left is None or right is None:
            continue
        op = node_text(op_node, sb)
        if op not in ("==", "!="):
            continue
        # size() compared against 0, in either order
        if (_is_size_call(left, sb) and _is_zero(right, sb)) or (
            _is_zero(left, sb) and _is_size_call(right, sb)
        ):
            ln, c, _, _ = __import__("rulesmith.parse", fromlist=["span"]).span(be)
            repl = "isEmpty()" if op == "==" else "!isEmpty()"
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": ln,
                    "col": c,
                    "message": "Use isEmpty() instead of comparing size() to 0",
                    "note": node_text(be, sb),
                    "help": "Replace size() " + op + " 0 with " + repl,
                }
            )
    return findings

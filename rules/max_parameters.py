# rule: a method must not declare more than 7 parameters

from rulesmith.parse import parse, find, span, node_text

RULE = "max-parameters"
MAX_PARAMS = 7


def analyze_source(src, file="<src>"):
    findings = []
    tree, src_bytes = parse(src)

    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        params = method.child_by_field_name("parameters")
        if params is None:
            continue
        count = len(
            [
                c
                for c in params.children
                if c.type in ("formal_parameter", "spread_parameter")
            ]
        )
        if count <= MAX_PARAMS:
            continue
        line, col, _, _ = span(method)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Method declares {count} parameters; max is {MAX_PARAMS}",
                "note": node_text(params, src_bytes),
                "help": "Group related parameters into a parameter object or builder",
            }
        )

    return findings

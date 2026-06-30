# rule: method names must be lowerCamelCase

from rulesmith.parse import parse, find, span, node_text

RULE = "method-name-lower-camel-case"


def _is_lower_camel(name):
    if not name:
        return False
    if not (name[0].isascii() and name[0].islower()):
        return False
    # lowerCamelCase: ascii letters and digits only, no underscores/symbols.
    return all(c.isascii() and c.isalnum() for c in name)


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    # constructor_declaration names mirror the class (PascalCase), so exclude them.
    for m in find(tree.root_node, "method_declaration"):
        name_node = m.child_by_field_name("name")
        if name_node is None:
            continue
        name = node_text(name_node, src_bytes)
        if _is_lower_camel(name):
            continue
        line, col, _el, _ec = span(name_node)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"method name '{name}' is not lowerCamelCase",
                "note": name,
                "help": "Start with a lowercase letter; use camelCase, no underscores or leading caps.",
            }
        )
    return findings

# rule: a class that overrides equals() must also override hashCode()

from rulesmith.parse import parse, find, node_text, span

RULE = "equals-hashcode-pair"


def _override_names(class_node):
    """Names of methods declared directly in this class body."""
    body = class_node.child_by_field_name("body")
    names = set()
    if body is None:
        return names
    for child in body.named_children:
        if child.type != "method_declaration":
            continue
        name = child.child_by_field_name("name")
        if name is not None:
            names.add((name, child))
    return names


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        equals_node = None
        has_hashcode = False
        for name_node, _method in _override_names(cls):
            mname = node_text(name_node, src_bytes)
            if mname == "equals":
                equals_node = name_node
            elif mname == "hashCode":
                has_hashcode = True
        if equals_node is not None and not has_hashcode:
            cls_name = cls.child_by_field_name("name")
            anchor = cls_name if cls_name is not None else equals_node
            line, col, _, _ = span(anchor)
            cls_label = (
                node_text(cls_name, src_bytes) if cls_name is not None else "<anon>"
            )
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Class '%s' overrides equals() but not hashCode()."
                    % cls_label,
                    "note": node_text(equals_node, src_bytes),
                    "help": "Override hashCode() whenever equals() is overridden so equal objects share a hash code.",
                }
            )
    return findings

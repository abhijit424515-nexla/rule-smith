# rule: Every field compared in equals must also be incorporated into hashCode, or equal objects can produce different hash codes.
# (authored by RuleSmith from the description above)

# rule: Every field compared in equals must also be incorporated into hashCode, or equal objects can produce different hash codes.
"""hashcode-uses-all-equals-fields: fields used in equals() must also appear in hashCode()."""

from rulesmith.parse import parse, find, span, node_text

RULE = "hashcode-uses-all-equals-fields"


def _class_fields(class_body, src_b):
    names = set()
    for fd in find(class_body, "field_declaration"):
        for decl in find(fd, "variable_declarator"):
            nm = decl.child_by_field_name("name")
            if nm is not None:
                names.add(node_text(nm, src_b))
    return names


def _method_named(class_body, name, src_b):
    for m in find(class_body, "method_declaration"):
        nm = m.child_by_field_name("name")
        if nm is not None and node_text(nm, src_b) == name:
            return m
    return None


def _fields_referenced(method, fields, src_b):
    # field names that appear as identifiers anywhere in the method body
    used = set()
    for ident in find(method, "identifier"):
        t = node_text(ident, src_b)
        if t in fields:
            used.add(t)
    return used


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        body = cls.child_by_field_name("body")
        if body is None:
            continue
        eq = _method_named(body, "equals", src_b)
        hc = _method_named(body, "hashCode", src_b)
        if eq is None or hc is None:
            continue
        fields = _class_fields(body, src_b)
        if not fields:
            continue
        eq_fields = _fields_referenced(eq, fields, src_b)
        hc_fields = _fields_referenced(hc, fields, src_b)
        missing = sorted(eq_fields - hc_fields)
        for fld in missing:
            ln, col, _, _ = span(hc)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": ln,
                    "col": col,
                    "message": f"field '{fld}' is compared in equals() but not used in hashCode()",
                    "note": f"equals uses {sorted(eq_fields)}; hashCode uses {sorted(hc_fields)}",
                    "help": f"incorporate '{fld}' into hashCode() so equal objects share a hash code",
                }
            )
    return findings

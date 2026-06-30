# rule: Flag a local or parameter declaration that shadows an in-scope field or enclosing variable with an unrelated initializer, a likely mistaken rebinding.
# (authored by RuleSmith from the description above)

# rule: Flag a local or parameter declaration that shadows an in-scope field or enclosing variable with an unrelated initializer, a likely mistaken rebinding.
"""Flag a local shadowing an in-scope field with an unrelated initializer (likely mistaken rebinding)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "variable-shadows-field-or-param"


def _field_names(root, src_b):
    names = set()
    for fd in find(root, "field_declaration"):
        for d in find(fd, "variable_declarator"):
            n = d.child_by_field_name("name")
            if n is not None:
                names.add(node_text(n, src_b))
    return names


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node
    fields = _field_names(root, src_b)
    if not fields:
        return []
    out = []
    for m in find(root, "method_declaration", "constructor_declaration"):
        for decl in find(m, "local_variable_declaration"):
            for d in find(decl, "variable_declarator"):
                name = d.child_by_field_name("name")
                value = d.child_by_field_name("value")
                if name is None or value is None:
                    continue
                vname = node_text(name, src_b)
                if vname not in fields:
                    continue
                # initializer that reads the shadowed name is an intentional copy, not a mistake
                refs = {node_text(i, src_b) for i in find(value, "identifier")}
                if value.type == "identifier":
                    refs.add(node_text(value, src_b))
                if vname in refs:
                    continue
                line, col = span(name)[0], span(name)[1]
                out.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"local '{vname}' shadows field '{vname}' with an unrelated initializer",
                        "note": f"field '{vname}' is in scope; the initializer does not reference it",
                        "help": f"rename the local, or write this.{vname} = ... if you meant to assign the field",
                        "judge": True,
                    }
                )
    return out

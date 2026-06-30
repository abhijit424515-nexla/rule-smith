# rule: Flag var / reassignable variable declarations because mutable bindings break equational reasoning and referential transparency.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "no-reassignable-var-declaration"


def _is_final(decl, src):
    for ch in decl.children:
        if ch.type == "modifiers":
            if "final" in node_text(ch, src).split():
                return True
    return False


def _is_var(decl, src):
    t = decl.child_by_field_name("type")
    return t is not None and node_text(t, src).strip() == "var"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    out = []
    for decl in find(tree.root_node, "local_variable_declaration"):
        is_final = _is_final(decl, src_bytes)
        is_var = _is_var(decl, src_bytes)
        # final + explicit type = immutable binding, ok. Anything else flags.
        if is_final and not is_var:
            continue
        line, col = span(decl)[0], span(decl)[1]
        reason = "var declaration" if is_var else "non-final (reassignable) declaration"
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Mutable local binding breaks equational reasoning / referential transparency",
                "note": reason
                + ": "
                + node_text(decl, src_bytes).splitlines()[0].strip(),
                "help": "Declare the binding 'final' with an explicit type.",
            }
        )
    return out

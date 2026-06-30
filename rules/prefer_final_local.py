# rule: A mutable local variable (var / non-final local) assigned exactly once and never reassigned should be val/final.
# (authored by RuleSmith from the description above)

# rule: A mutable local variable (var / non-final local) assigned exactly once and never reassigned should be val/final.
from rulesmith.parse import parse, find, span, node_text

RULE = "prefer-final-local"


def _modifier_words(decl, sb):
    mods = next((c for c in decl.children if c.type == "modifiers"), None)
    return node_text(mods, sb).split() if mods is not None else []


def _reassigned(method_ts, name, sb):
    # bare `name = ...` / `name += ...` (field_access like this.name does NOT
    # match -- left is field_access, not identifier).
    for asg in find(method_ts, "assignment_expression"):
        left = asg.child_by_field_name("left")
        if (
            left is not None
            and left.type == "identifier"
            and node_text(left, sb) == name
        ):
            return True
    # name++ / --name etc. are update_expression, not assignment_expression.
    for upd in find(method_ts, "update_expression"):
        for ident in find(upd, "identifier"):
            if node_text(ident, sb) == name:
                return True
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        body = method.child_by_field_name("body")
        if body is None:
            continue
        for decl in find(body, "local_variable_declaration"):
            if "final" in _modifier_words(decl, sb):
                continue
            for vd in find(decl, "variable_declarator"):
                name_node = vd.child_by_field_name("name")
                value = vd.child_by_field_name("value")
                # ponytail: require an initializer so "assigned exactly once" is
                # the declarator itself -- avoids path analysis for blank finals.
                if name_node is None or value is None:
                    continue
                name = node_text(name_node, sb)
                if _reassigned(method, name, sb):
                    continue
                ln, c, *_ = span(name_node)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": ln,
                        "col": c,
                        "message": f"Local '{name}' is assigned once and never reassigned; declare it final.",
                        "note": f"local '{name}' has a single definition (its initializer) and no reassignment in the method",
                        "help": f"Add 'final' to the declaration of '{name}'.",
                    }
                )
    return findings

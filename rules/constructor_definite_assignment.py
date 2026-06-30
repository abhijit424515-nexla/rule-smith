# rule: Every non-nullable instance field must be definitely assigned on every path through each constructor before that constructor returns.
# (authored by RuleSmith from the description above)

# rule: Every non-nullable instance field must be definitely assigned on every path through each constructor before that constructor returns.
from rulesmith.parse import parse, find, span, node_text

RULE = "constructor-definite-assignment"

# Any of these between an assignment and the constructor body means the
# assignment is conditional, so it does not run on every path.
CONDITIONAL_TYPES = {
    "if_statement",
    "for_statement",
    "enhanced_for_statement",
    "while_statement",
    "do_statement",
    "switch_expression",
    "switch_statement",
    "try_statement",
    "catch_clause",
    "ternary_expression",
    "lambda_expression",
}


def _modifiers(node):
    return next((c for c in node.children if c.type == "modifiers"), None)


def _declarator(decl):
    for vd in find(decl, "variable_declarator"):
        if vd.child_by_field_name("name") is not None:
            return vd
    return None


def _assign_target(assign, sb):
    left = assign.child_by_field_name("left")
    if left is None:
        return None
    if left.type == "field_access":  # this.name
        f = left.child_by_field_name("field")
        return node_text(f, sb) if f is not None else None
    if left.type == "identifier":  # bare name
        return node_text(left, sb)
    return None


def _unconditionally_assigned(cbody, sb):
    result = set()
    for assign in find(cbody, "assignment_expression"):
        op = assign.child_by_field_name("operator")
        if op is not None and node_text(op, sb) != "=":
            continue  # compound assign assumes a prior value
        target = _assign_target(assign, sb)
        if target is None:
            continue
        cond = False
        n = assign.parent
        while n is not None and n != cbody:
            if n.type in CONDITIONAL_TYPES:
                cond = True
                break
            n = n.parent
        if not cond:
            result.add(target)
    return result


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        body = cls.child_by_field_name("body")
        if body is None:
            continue

        # non-nullable instance fields that need definite assignment
        must = {}
        for decl in body.children:
            if decl.type != "field_declaration":
                continue
            mods = _modifiers(decl)
            modtext = node_text(mods, sb) if mods is not None else ""
            if "static" in modtext.split():
                continue
            if "@Nullable" in modtext:
                continue
            vd = _declarator(decl)
            if vd is None:
                continue
            if vd.child_by_field_name("value") is not None:
                continue  # initialized at declaration
            must[node_text(vd.child_by_field_name("name"), sb)] = decl

        if not must:
            continue

        for ctor in [c for c in body.children if c.type == "constructor_declaration"]:
            cbody = ctor.child_by_field_name("body")
            if cbody is None:
                continue
            # ponytail: structural definite-assignment; treats only top-level
            # (unconditional) assignments as definite. Misses if/else-both-branches
            # and this(...) delegation -- swap to CFG dominators if those matter.
            assigned = _unconditionally_assigned(cbody, sb)
            for fname in must:
                if fname in assigned:
                    continue
                ln, c, *_ = span(ctor)
                cname = node_text(ctor.child_by_field_name("name"), sb)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": ln,
                        "col": c,
                        "message": f"Field '{fname}' is not definitely assigned on every path through constructor '{cname}'.",
                        "note": f"constructor '{cname}' returns without assigning non-nullable field '{fname}' on all paths",
                        "help": f"Assign this.{fname} unconditionally in the constructor body, not only inside a branch.",
                    }
                )
    return findings

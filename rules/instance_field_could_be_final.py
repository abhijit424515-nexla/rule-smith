# rule: Instance fields assigned only during construction and never reassigned should be declared final to minimize mutability.
# (authored by RuleSmith from the description above)

# rule: Instance fields assigned only during construction and never reassigned should be declared final to minimize mutability.
from rulesmith.parse import parse, find, span, node_text

RULE = "instance-field-could-be-final"


def _modifiers(node):
    return next((c for c in node.children if c.type == "modifiers"), None)


def _modtext(node, sb):
    m = _modifiers(node)
    return node_text(m, sb) if m is not None else ""


def _target(left, sb):
    if left is None:
        return None
    if left.type == "field_access":  # this.f / obj.f
        f = left.child_by_field_name("field")
        return node_text(f, sb) if f is not None else None
    if left.type == "identifier":  # bare f
        return node_text(left, sb)
    return None


def _enclosing_kind(node, body):
    """Where does this write live, relative to the class body?
    'ctor'/'init' == construction-time, 'method' == post-construction."""
    n = node.parent
    while n is not None and n is not body:
        if n.type == "constructor_declaration":
            return "ctor"
        if n.type == "method_declaration":
            return "method"
        n = n.parent
    return "init"  # field initializer or instance-initializer block


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        body = cls.child_by_field_name("body")
        if body is None:
            continue

        # candidate fields: non-static, non-final instance fields
        candidates = {}  # name -> name_node
        stats = {}  # name -> {init, ctor, method, compound}
        for decl in body.children:
            if decl.type != "field_declaration":
                continue
            toks = _modtext(decl, sb).split()
            if "static" in toks or "final" in toks:
                continue
            for vd in find(decl, "variable_declarator"):
                nm = vd.child_by_field_name("name")
                if nm is None:
                    continue
                name = node_text(nm, sb)
                candidates[name] = nm
                stats[name] = {
                    "init": False,
                    "ctor": False,
                    "method": False,
                    "compound": False,
                }
                if vd.child_by_field_name("value") is not None:
                    stats[name]["init"] = True

        if not candidates:
            continue

        # plain/compound assignments anywhere in the class
        for asg in find(body, "assignment_expression"):
            t = _target(asg.child_by_field_name("left"), sb)
            if t not in stats:
                continue
            op = asg.child_by_field_name("operator")
            if op is not None and node_text(op, sb) != "=":
                stats[t]["compound"] = True  # read-modify-write: not final-safe
                continue
            kind = _enclosing_kind(asg, body)
            stats[t]["method" if kind == "method" else "ctor"] = True

        # ++ / -- updates are also read-modify-write
        for upd in find(body, "update_expression"):
            for ch in upd.children:
                t = _target(ch, sb)
                if t in stats:
                    stats[t]["compound"] = True

        for name, s in stats.items():
            if s["compound"] or s["method"]:
                continue
            if not (s["init"] or s["ctor"]):
                continue  # never assigned at construction; leave it alone
            ln, c, *_ = span(candidates[name])
            where = (
                "its declaration" if s["init"] and not s["ctor"] else "the constructor"
            )
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": ln,
                    "col": c,
                    "message": f"Instance field '{name}' is assigned only during construction and never reassigned; declare it final.",
                    "note": f"field '{name}' is written only at {where} and never mutated afterward",
                    "help": f"Add 'final' to the declaration of '{name}'.",
                }
            )
    return findings

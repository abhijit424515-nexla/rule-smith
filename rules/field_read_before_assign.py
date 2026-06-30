# rule: A non-nullable field must not be read (or leaked via this-escape or method call) before it has been assigned earlier in the same constructor.
# (authored by RuleSmith from the description above)

# rule: A non-nullable field must not be read (or leaked via this-escape or method call) before it has been assigned earlier in the same constructor.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "field-read-before-assign"


def _modifiers(node):
    return next((c for c in node.children if c.type == "modifiers"), None)


def _target_name(assign, sb):
    """Field name written by `assign` (this.x = .. or x = ..), else None."""
    left = assign.child_by_field_name("left")
    if left is None:
        return None
    if left.type == "field_access":
        obj = left.child_by_field_name("object")
        f = left.child_by_field_name("field")
        if obj is not None and obj.type == "this" and f is not None:
            return node_text(f, sb)
    elif left.type == "identifier":
        return node_text(left, sb)
    return None


def _must_fields(body, sb):
    """Non-nullable, non-static instance fields not initialized at declaration."""
    must = set()
    for decl in body.children:
        if decl.type != "field_declaration":
            continue
        mods = _modifiers(decl)
        modtext = node_text(mods, sb) if mods is not None else ""
        if "static" in modtext.split() or "@Nullable" in modtext:
            continue
        for vd in find(decl, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is None or vd.child_by_field_name("value") is not None:
                continue
            must.add(node_text(nm, sb))
    return must


def _is_write_left(fa):
    p = fa.parent
    return (
        p is not None
        and p.type == "assignment_expression"
        and p.child_by_field_name("left") == fa
    )


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    out = []
    for cls in find(tree.root_node, "class_declaration"):
        body = cls.child_by_field_name("body")
        if body is None:
            continue
        must = _must_fields(body, sb)
        if not must:
            continue
        for ctor in [c for c in body.children if c.type == "constructor_declaration"]:
            cbody = ctor.child_by_field_name("body")
            if cbody is None:
                continue
            # ponytail: source-order analysis (byte offsets), not a CFG. Misses
            # branch/loop ordering; assignment "takes effect" at end of its
            # statement so a self-referential RHS read still flags. Reads are
            # only the `this.field` form -- bare `field` reads are not tracked.
            events = []
            for a in find(cbody, "assignment_expression"):
                op = a.child_by_field_name("operator")
                if op is not None and node_text(op, sb) != "=":
                    continue
                nm = _target_name(a, sb)
                if nm in must:
                    events.append((a.end_byte, 0, "assign", nm, a))
            for fa in find(cbody, "field_access"):
                obj = fa.child_by_field_name("object")
                f = fa.child_by_field_name("field")
                if obj is None or obj.type != "this" or f is None:
                    continue
                if _is_write_left(fa):
                    continue
                nm = node_text(f, sb)
                if nm in must:
                    events.append((fa.start_byte, 1, "read", nm, fa))
            for t in find(cbody, "this"):
                if t.parent is not None and t.parent.type == "argument_list":
                    events.append((t.start_byte, 1, "escape", None, t))

            events.sort(key=lambda e: (e[0], e[1]))
            assigned = set()
            for _, _, kind, nm, node in events:
                if kind == "assign":
                    assigned.add(nm)
                elif kind == "read":
                    if nm not in assigned:
                        line, col, _, _ = span(node)
                        out.append(
                            {
                                "rule": RULE,
                                "file": file,
                                "line": line,
                                "col": col,
                                "message": f"non-nullable field '{nm}' is read before it is assigned in this constructor",
                                "note": node_text(node, sb),
                                "help": f"assign this.{nm} before reading it, or move the read after the assignment",
                            }
                        )
                else:  # escape
                    leaked = sorted(must - assigned)
                    if leaked:
                        line, col, _, _ = span(node)
                        out.append(
                            {
                                "rule": RULE,
                                "file": file,
                                "line": line,
                                "col": col,
                                "message": "`this` escapes the constructor before non-nullable field(s) "
                                + ", ".join(f"'{x}'" for x in leaked)
                                + " are assigned",
                                "note": node_text(node.parent.parent, sb)
                                if node.parent is not None
                                and node.parent.parent is not None
                                else "this",
                                "help": "assign all non-nullable fields before passing `this` to another method",
                            }
                        )
    return out

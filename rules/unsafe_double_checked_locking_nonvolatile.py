# rule: Double-checked lazy init must declare the guarded reference volatile (or use the holder idiom); without it the publication is broken under the JMM and can expose a partially constructed object.
# (authored by RuleSmith from the description above)

# rule: Double-checked lazy init must declare the guarded reference volatile (or use the holder idiom); without it the publication is broken under the JMM and can expose a partially constructed object.
"""Flag double-checked locking that assigns a non-volatile field (broken JMM publication)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "unsafe-double-checked-locking-nonvolatile"


def _last_ident(node, src_b):
    if node is None:
        return None
    ids = find(node, "identifier")
    return node_text(ids[-1], src_b) if ids else None


def _refs_null_check(cond, name, src_b):
    # condition contains a `name == null` / `name != null` comparison
    if cond is None:
        return False
    for be in find(cond, "binary_expression"):
        op = be.child_by_field_name("operator")
        if op is None or node_text(op, src_b) not in ("==", "!="):
            continue
        left = be.child_by_field_name("left")
        right = be.child_by_field_name("right")
        sides = [node_text(left, src_b), node_text(right, src_b)]
        if "null" in sides and (
            _last_ident(left, src_b) == name or _last_ident(right, src_b) == name
        ):
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node

    volatile_fields, field_names = set(), set()
    for fd in find(root, "field_declaration"):
        mods_text = ""
        for c in fd.children:
            if c.type == "modifiers":
                mods_text = node_text(c, src_b)
                break
        is_vol = "volatile" in mods_text
        for vd in find(fd, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is None:
                continue
            n = node_text(nm, src_b)
            field_names.add(n)
            if is_vol:
                volatile_fields.add(n)

    findings = []
    for m in find(root, "method_declaration", "constructor_declaration"):
        syncs = find(m, "synchronized_statement")
        if not syncs:
            continue
        ifs = find(m, "if_statement")
        for sync in syncs:
            flagged = False
            for a in find(sync, "assignment_expression"):
                if flagged:
                    break
                left = a.child_by_field_name("left")
                name = _last_ident(left, src_b)
                if name is None or name not in field_names or name in volatile_fields:
                    continue
                # double-check: >=2 null-checks on `name` in the method (outer + inner)
                nchk = sum(
                    1
                    for iff in ifs
                    if _refs_null_check(
                        iff.child_by_field_name("condition"), name, src_b
                    )
                )
                if nchk < 2:
                    continue
                line, col, _, _ = span(a)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"double-checked locking assigns non-volatile field '{name}'",
                        "note": f"field '{name}' is not declared volatile; {nchk} null-checks guard a synchronized assignment",
                        "help": f"declare '{name}' volatile, or use the static holder idiom",
                    }
                )
                flagged = True
    return findings

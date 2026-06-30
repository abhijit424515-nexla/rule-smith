# rule: A reference that may be null on some control-flow path must not be dereferenced (field/method access) without a preceding null guard that dominates the use.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "null-deref-needs-dominating-guard"


def _is_null(node, src):
    return node is not None and (
        node.type == "null_literal" or node_text(node, src) == "null"
    )


def _ident(node, src, name):
    return (
        node is not None and node.type == "identifier" and node_text(node, src) == name
    )


def _maybe_null_vars(method, src):
    """Locals that may hold null on some path: declared = null, or assigned = null."""
    names = set()
    for d in find(method, "local_variable_declaration"):
        for vd in find(d, "variable_declarator"):
            if _is_null(vd.child_by_field_name("value"), src):
                nm = vd.child_by_field_name("name")
                if nm is not None:
                    names.add(node_text(nm, src))
    for a in find(method, "assignment_expression"):
        left = a.child_by_field_name("left")
        if (
            left is not None
            and left.type == "identifier"
            and _is_null(a.child_by_field_name("right"), src)
        ):
            names.add(node_text(left, src))
    return names


def _guard_op(cond, src, name):
    """Return '==' or '!=' if cond contains a `name <op> null` comparison, else None."""
    if cond is None:
        return None
    for b in find(cond, "binary_expression"):
        opn = b.child_by_field_name("operator")
        if opn is None:
            continue
        op = node_text(opn, src)
        if op not in ("==", "!="):
            continue
        ln = b.child_by_field_name("left")
        r = b.child_by_field_name("right")
        if (_ident(ln, src, name) and _is_null(r, src)) or (
            _ident(r, src, name) and _is_null(ln, src)
        ):
            return op
    return None


def _contains(region, node):
    return (
        region is not None
        and region.start_byte <= node.start_byte
        and node.end_byte <= region.end_byte
    )


def _exits(block):
    return len(find(block, "return_statement", "throw_statement")) > 0


def _guarded(use, method, src, name):
    """True if a null guard for `name` dominates `use` (structural dominance)."""
    for iff in find(method, "if_statement"):
        op = _guard_op(iff.child_by_field_name("condition"), src, name)
        if op is None:
            continue
        cons = iff.child_by_field_name("consequence")
        alt = iff.child_by_field_name("alternative")
        if op == "!=" and _contains(cons, use):
            return True
        if op == "==":
            # use inside else branch
            if alt is not None and _contains(alt, use):
                return True
            # early-exit guard: `if (x == null) { return/throw; }` then use after it
            if (
                alt is None
                and _exits(cons)
                and use.start_byte >= iff.end_byte
                and _contains(method, use)
            ):
                return True
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        names = _maybe_null_vars(m, sb)
        if not names:
            continue
        sites = []
        for mi in find(m, "method_invocation"):
            obj = mi.child_by_field_name("object")
            if (
                obj is not None
                and obj.type == "identifier"
                and node_text(obj, sb) in names
            ):
                sites.append((node_text(obj, sb), obj, mi))
        for fa in find(m, "field_access"):
            obj = fa.child_by_field_name("object")
            if (
                obj is not None
                and obj.type == "identifier"
                and node_text(obj, sb) in names
            ):
                sites.append((node_text(obj, sb), obj, fa))
        for nm, obj, use in sites:
            if _guarded(use, m, sb, nm):
                continue
            line, col, _, _ = span(obj)
            out.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "'"
                    + nm
                    + "' may be null here and is dereferenced without a dominating null guard",
                    "note": node_text(use, sb),
                    "help": "Add a check like `if ("
                    + nm
                    + " != null)` that dominates this access, or an early `if ("
                    + nm
                    + " == null) return;` guard before it",
                }
            )
    return out

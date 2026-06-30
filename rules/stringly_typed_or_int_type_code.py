# rule: Flag String/int fields or parameters (often named Type/Code/Status/Role) compared against constants or literals to branch behavior; model as an enum or sealed type.
# (authored by RuleSmith from the description above)

# rule: Flag String/int fields or parameters (often named Type/Code/Status/Role) compared against constants or literals to branch behavior; model as an enum or sealed type.
"""Stringly/int-typed type/status/code/role fields compared against literals should be enums."""

from rulesmith.parse import parse, find, span, node_text

RULE = "stringly-typed-or-int-type-code"

_SUFFIXES = ("type", "code", "status", "role", "state", "kind")
_TYPES = ("String", "int", "Integer")


def _is_candidate_name(name):
    n = name.lower()
    return any(n.endswith(s) for s in _SUFFIXES)


def _collect_candidates(root, src_b):
    names = set()
    for decl in find(root, "field_declaration", "formal_parameter"):
        t = decl.child_by_field_name("type")
        if t is None or node_text(t, src_b) not in _TYPES:
            continue
        if decl.type == "formal_parameter":
            nm = decl.child_by_field_name("name")
            if nm is not None and _is_candidate_name(node_text(nm, src_b)):
                names.add(node_text(nm, src_b))
        else:  # field_declaration -> variable_declarator(s)
            for vd in find(decl, "variable_declarator"):
                nm = vd.child_by_field_name("name")
                if nm is not None and _is_candidate_name(node_text(nm, src_b)):
                    names.add(node_text(nm, src_b))
    return names


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node
    cands = _collect_candidates(root, src_b)
    if not cands:
        return []
    findings = []
    seen = set()

    def emit(node, var, literal):
        line, col = span(node)[0], span(node)[1]
        key = (line, col)
        if key in seen:
            return
        seen.add(key)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"'{var}' is a stringly/int-typed code compared against literal {literal} to branch behavior; model as an enum or sealed type.",
                "note": node_text(node, src_b),
                "help": f"Replace '{var}' with an enum and compare enum constants instead of {literal}.",
            }
        )

    # x.equals("LITERAL") / x.equalsIgnoreCase("LITERAL")
    for mi in find(root, "method_invocation"):
        name = mi.child_by_field_name("name")
        obj = mi.child_by_field_name("object")
        if name is None or obj is None:
            continue
        if node_text(name, src_b) not in ("equals", "equalsIgnoreCase"):
            continue
        if obj.type != "identifier" or node_text(obj, src_b) not in cands:
            continue
        args = mi.child_by_field_name("arguments")
        lits = find(args, "string_literal") if args is not None else []
        if lits:
            emit(mi, node_text(obj, src_b), node_text(lits[0], src_b))

    # x == "LIT" / x == 3 / x != ...
    for be in find(root, "binary_expression"):
        op = be.child_by_field_name("operator")
        if op is None or node_text(op, src_b) not in ("==", "!="):
            continue
        left = be.child_by_field_name("left")
        right = be.child_by_field_name("right")
        ident, lit = None, None
        for a, b in ((left, right), (right, left)):
            if (
                a is not None
                and a.type == "identifier"
                and node_text(a, src_b) in cands
            ):
                if b is not None and b.type in (
                    "string_literal",
                    "decimal_integer_literal",
                ):
                    ident, lit = a, b
        if ident is not None:
            emit(be, node_text(ident, src_b), node_text(lit, src_b))

    return findings

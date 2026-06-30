# rule: Null-checking a mutable (non-final) field and then dereferencing it is a TOCTOU race; capture into a local first, then check and use the local.
# (authored by RuleSmith from the description above)

# rule: null-checking a non-final field then dereferencing it is a TOCTOU race; capture into a local first

from rulesmith.parse import parse, find, span, node_text

RULE = "field-null-check-toctou"


def _is_final(fd, src_bytes):
    for c in fd.children:
        if c.type == "modifiers":
            return "final" in {node_text(m, src_bytes) for m in c.children}
    return False


def _base_name(text):
    t = text.strip()
    if t.startswith("this."):
        t = t[len("this.") :]
    return t


def _null_checked_fields(cond, src_bytes, nonfinal):
    out = set()
    candidates = list(find(cond, "binary_expression"))
    if cond.type == "binary_expression":
        candidates.append(cond)
    for be in candidates:
        op = be.child_by_field_name("operator")
        if op is None or node_text(op, src_bytes) != "!=":
            continue
        left = be.child_by_field_name("left")
        right = be.child_by_field_name("right")
        if left is None or right is None:
            continue
        if left.type == "null_literal":
            ref = right
        elif right.type == "null_literal":
            ref = left
        else:
            continue
        if ref.type not in ("identifier", "field_access"):
            continue
        base = _base_name(node_text(ref, src_bytes))
        if base in nonfinal:
            out.add(base)
    return out


def _derefs(scope, src_bytes, name):
    for kind in ("method_invocation", "field_access", "array_access"):
        for node in find(scope, kind):
            obj = node.child_by_field_name("object") or node.child_by_field_name(
                "array"
            )
            if obj is not None and _base_name(node_text(obj, src_bytes)) == name:
                return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    root = tree.root_node

    nonfinal = set()
    for fd in find(root, "field_declaration"):
        if _is_final(fd, src_bytes):
            continue
        for vd in find(fd, "variable_declarator"):
            name = vd.child_by_field_name("name")
            if name is not None:
                nonfinal.add(node_text(name, src_bytes))

    findings = []
    for m in find(root, "method_declaration", "constructor_declaration"):
        for iff in find(m, "if_statement"):
            cond = iff.child_by_field_name("condition")
            cons = iff.child_by_field_name("consequence")
            if cond is None or cons is None:
                continue
            for fld in sorted(_null_checked_fields(cond, src_bytes, nonfinal)):
                if _derefs(cons, src_bytes, fld):
                    line, col, _, _ = span(iff)
                    findings.append(
                        {
                            "rule": RULE,
                            "file": file,
                            "line": line,
                            "col": col,
                            "message": (
                                "Null-checking non-final field '%s' then dereferencing "
                                "it inside the guard is a TOCTOU race" % fld
                            ),
                            "note": node_text(cond, src_bytes).strip(),
                            "help": (
                                "Capture the field into a local first, then null-check "
                                "and dereference the local."
                            ),
                        }
                    )
                    break
    return findings

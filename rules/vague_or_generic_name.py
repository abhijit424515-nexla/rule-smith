# rule: Flag identifiers too generic to convey meaning (data, info, tmp, manager, doIt, value, obj) when used in non-trivial scopes.
# (authored by RuleSmith from the description above)

# rule: Flag identifiers too generic to convey meaning (data, info, tmp, manager, doIt, value, obj) when used in non-trivial scopes.
"""Flag vague/generic identifiers (data, info, tmp, manager, doIt, value, obj) in non-trivial scopes."""

from rulesmith.parse import parse, find, span, node_text

RULE = "vague-or-generic-name"

GENERIC = {"data", "info", "tmp", "manager", "doit", "value", "obj"}
NONTRIVIAL_STMTS = (
    3  # method body with >= this many statements is a "non-trivial scope"
)


def _base(name: str) -> str:
    """Normalize an identifier for matching: lowercase, drop trailing digits (data2 -> data)."""
    return name.lower().rstrip("0123456789")


def _is_nontrivial(body) -> bool:
    return body is not None and len(body.named_children) >= NONTRIVIAL_STMTS


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    seen = set()

    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        body = method.child_by_field_name("body")
        if not _is_nontrivial(body):
            continue

        # candidate name-bearing nodes: the method name, each parameter, each local var
        candidates = []
        mname = method.child_by_field_name("name")
        if mname is not None:
            candidates.append(("method", mname))
        for p in find(method, "formal_parameter"):
            n = p.child_by_field_name("name")
            if n is not None:
                candidates.append(("parameter", n))
        for d in find(method, "variable_declarator"):
            n = d.child_by_field_name("name")
            if n is not None:
                candidates.append(("local variable", n))

        for kind, node in candidates:
            text = node_text(node, src_b)
            if _base(text) not in GENERIC:
                continue
            line, col, *_ = span(node)
            key = (line, col)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"{kind} '{text}' is too generic to convey meaning",
                    "note": f"generic identifier '{text}' in a non-trivial scope ({len(body.named_children)} statements)",
                    "help": "rename to describe what it holds or does (e.g. the entity, unit, or role it represents)",
                }
            )

    return findings

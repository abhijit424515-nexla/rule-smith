# rule: A switch over a sealed hierarchy or enum must be compiler-checked exhaustive; flag both omitted cases without default and a default/catch-all that silently absorbs newly added variants.
# (authored by RuleSmith from the description above)

# rule: A switch over a sealed hierarchy or enum must be compiler-checked exhaustive; flag both omitted cases without default and a default/catch-all that silently absorbs newly added variants.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "exhaustive-sealed-enum-switch"


def _registry(root, src_bytes):
    """type name -> (kind, set(variant names)). kind in {"enum","sealed"}."""
    reg = {}
    for e in find(root, "enum_declaration"):
        name = e.child_by_field_name("name")
        if name is None:
            continue
        variants = {
            node_text(c.child_by_field_name("name"), src_bytes)
            for c in find(e, "enum_constant")
            if c.child_by_field_name("name") is not None
        }
        reg[node_text(name, src_bytes)] = ("enum", variants)

    for d in find(root, "class_declaration", "interface_declaration"):
        mods = next((c for c in d.children if c.type == "modifiers"), None)
        if mods is None or "sealed" not in node_text(mods, src_bytes):
            continue
        name = d.child_by_field_name("name")
        if name is None:
            continue
        permits = next((c for c in d.children if c.type == "permits"), None)
        if permits is None:
            continue
        variants = {node_text(t, src_bytes) for t in find(permits, "type_identifier")}
        reg[node_text(name, src_bytes)] = ("sealed", variants)
    return reg


def _enclosing(node):
    p = node.parent
    while p is not None and p.type not in (
        "method_declaration",
        "constructor_declaration",
    ):
        p = p.parent
    return p


def _selector_type(switch_node, src_bytes):
    """Resolve the static type name of the switch selector identifier."""
    paren = next(
        (c for c in switch_node.children if c.type == "parenthesized_expression"),
        None,
    )
    if paren is None:
        return None
    ids = find(paren, "identifier")
    if not ids:
        return None
    var = node_text(ids[0], src_bytes)

    scope = _enclosing(switch_node) or switch_node
    for fp in find(scope, "formal_parameter"):
        nm, ty = fp.child_by_field_name("name"), fp.child_by_field_name("type")
        if nm is not None and ty is not None and node_text(nm, src_bytes) == var:
            return node_text(ty, src_bytes)
    for lv in find(scope, "local_variable_declaration"):
        ty = lv.child_by_field_name("type")
        for vd in find(lv, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None and ty is not None and node_text(nm, src_bytes) == var:
                return node_text(ty, src_bytes)
    return None


def analyze_source(src, file="<src>") -> list:
    tree, src_bytes = parse(src)
    root = tree.root_node
    reg = _registry(root, src_bytes)
    findings = []

    for sw in find(root, "switch_expression", "switch_statement"):
        ty = _selector_type(sw, src_bytes)
        if ty is None or ty not in reg:
            continue
        kind, declared = reg[ty]

        labels = find(sw, "switch_label", "default_label")
        has_default = any(
            lbl.type == "default_label"
            or any(c.type == "default" for c in lbl.children)
            for lbl in labels
        )
        names = {
            node_text(n, src_bytes)
            for lbl in labels
            for n in find(lbl, "identifier", "type_identifier")
        }
        covered = declared & names
        missing = declared - covered

        line, col, *_ = span(sw)
        if has_default:
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"default/catch-all on {kind} switch silently absorbs newly added variants",
                    "note": f"switch over {kind} {ty}; a new variant would fall into default instead of a compile error",
                    "help": "Drop the default and list every variant so the compiler enforces exhaustiveness",
                }
            )
        elif missing:
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"non-exhaustive {kind} switch with no default omits cases",
                    "note": f"switch over {kind} {ty} omits: {', '.join(sorted(missing))}",
                    "help": "Cover every variant (no default) so the compiler checks exhaustiveness",
                }
            )

    return findings

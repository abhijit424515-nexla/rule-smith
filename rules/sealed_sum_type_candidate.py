# rule: Flag a class where a kind/status field plus several nullable fields are valid only in mutually exclusive combinations; model as a sealed sum type.
# (authored by RuleSmith from the description above)

# rule: Flag a class where a kind/status field plus several nullable fields are valid only in mutually exclusive combinations; model as a sealed sum type.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "sealed-sum-type-candidate"

# A discriminator field is a "what kind am I" tag.
_DISCRIMINATOR_HINTS = ("kind", "type", "status", "state", "variant", "tag", "mode")

# tree-sitter-java primitive type node kinds.
_PRIMITIVE = {"integral_type", "floating_point_type", "boolean_type", "void_type"}

_MIN_NULLABLE = 3  # "several" nullable fields


def _fields(class_node):
    """Direct field_declarations of this class body (skip nested classes)."""
    body = class_node.child_by_field_name("body")
    if body is None:
        return []
    return [c for c in body.children if c.type == "field_declaration"]


def _field_names_and_type(fd, src):
    t = fd.child_by_field_name("type")
    names = [
        node_text(d.child_by_field_name("name"), src)
        for d in find(fd, "variable_declarator")
        if d.child_by_field_name("name") is not None
    ]
    return t, names


def _refs(node, name, src):
    return name in {node_text(i, src) for i in find(node, "identifier")}


def _branches_on(class_node, name, src):
    """A switch on the discriminator, or an if whose condition tests it."""
    for sw in find(class_node, "switch_expression", "switch_statement"):
        cond = sw.child_by_field_name("condition")
        if cond is not None and _refs(cond, name, src):
            return sw
    for ifs in find(class_node, "if_statement"):
        cond = ifs.child_by_field_name("condition")
        if cond is not None and _refs(cond, name, src):
            return ifs
    return None


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        discriminator = None  # (name, line, col)
        nullable = []
        for fd in _fields(cls):
            t, names = _field_names_and_type(fd, src_bytes)
            if t is None or not names:
                continue
            is_ref = t.type not in _PRIMITIVE
            for nm in names:
                low = nm.lower()
                if discriminator is None and any(
                    h in low for h in _DISCRIMINATOR_HINTS
                ):
                    line, col, _, _ = span(fd)
                    discriminator = (nm, line, col)
                elif is_ref:
                    nullable.append(nm)
        if discriminator is None or len(nullable) < _MIN_NULLABLE:
            continue
        name, line, col = discriminator
        branch = _branches_on(cls, name, src_bytes)
        if branch is None:
            continue
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Class has discriminator '%s' plus %d nullable fields gated by it; valid states are mutually exclusive."
                % (name, len(nullable)),
                "note": node_text(branch, src_bytes)[:200],
                "help": "Model the variants as a sealed interface/record hierarchy so each state owns only its fields.",
            }
        )
    return findings

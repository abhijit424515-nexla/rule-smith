# rule: Operations whose meaning depends on sign interpretation (/, %, <, >, >>) must not be applied to @Unsigned values, and an operation must not mix @Signed and @Unsigned operands; use the unsigned utility methods.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "unsigned-sign-sensitive-ops"

# Operators whose result meaning depends on sign interpretation.
SIGN_DEP = {"/", "%", "<", ">", ">>"}


def _annot_names(node, src):
    names = []
    for a in find(node, "marker_annotation", "annotation"):
        nm = a.child_by_field_name("name")
        if nm is not None:
            names.append(node_text(nm, src).split(".")[-1])
    return names


def _sign_of(names):
    if "Unsigned" in names:
        return "unsigned"
    if "Signed" in names:
        return "signed"
    return None


def _collect_signs(tree, src):
    """Map declared variable name -> 'unsigned'/'signed' from annotations."""
    signs = {}
    for decl in find(tree.root_node, "formal_parameter"):
        s = _sign_of(_annot_names(decl, src))
        nm = decl.child_by_field_name("name")
        if s and nm is not None:
            signs[node_text(nm, src)] = s
    for decl in find(tree.root_node, "local_variable_declaration"):
        s = _sign_of(_annot_names(decl, src))
        if not s:
            continue
        for vd in find(decl, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                signs[node_text(nm, src)] = s
    return signs


def _operand_sign(node, src, signs):
    if node is not None and node.type == "identifier":
        return signs.get(node_text(node, src))
    return None


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    signs = _collect_signs(tree, src_bytes)
    findings = []
    for be in find(tree.root_node, "binary_expression"):
        op_node = be.child_by_field_name("operator")
        left = be.child_by_field_name("left")
        right = be.child_by_field_name("right")
        if op_node is None:
            continue
        op = node_text(op_node, src_bytes)
        ls = _operand_sign(left, src_bytes, signs)
        rs = _operand_sign(right, src_bytes, signs)
        line, col, _, _ = span(be)
        mixed = ls is not None and rs is not None and ls != rs
        if op in SIGN_DEP and (ls == "unsigned" or rs == "unsigned"):
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": (
                        "Sign-sensitive operator '%s' applied to @Unsigned value; "
                        "use the unsigned utility methods (e.g. Integer.divideUnsigned/compareUnsigned)."
                        % op
                    ),
                    "note": node_text(be, src_bytes),
                    "help": "Replace '%s' with the matching unsigned helper for @Unsigned operands."
                    % op,
                }
            )
        elif mixed:
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Operation '%s' mixes @Signed and @Unsigned operands."
                    % op,
                    "note": node_text(be, src_bytes),
                    "help": "Do not mix @Signed and @Unsigned operands; convert explicitly first.",
                }
            )
    return findings

# rule: Operations whose meaning depends on sign interpretation (/, %, <, >, >>) must not be applied to @Unsigned values, and an operation must not mix @Signed and @Unsigned operands; use the unsigned utility methods.
# (authored by RuleSmith from the description above)

# rule: Operations whose meaning depends on sign interpretation (/, %, <, >, >>) must not be applied to @Unsigned values, and an operation must not mix @Signed and @Unsigned operands; use the unsigned utility methods.
# (authored by RuleSmith from the description above)

"""Rule: unsigned-sign-op (detective).

Tracks variables/parameters/fields annotated ``@Unsigned`` or ``@Signed``
and flags binary expressions that interpret bits as signed:

  * a sign-dependent operator (``/ % < > >>``) with an ``@Unsigned`` operand;
  * any binary op that mixes a ``@Signed`` and an ``@Unsigned`` operand.

Sign tracking is purely declaration-driven (no inference): we map each
declared identifier to the marker annotation on its declaration, then look
up the identifiers used as operands. Fix: use the unsigned utility methods
(e.g. ``Integer.divideUnsigned``, ``Integer.compareUnsigned``,
``>>>`` for an unsigned shift).
"""

from rulesmith.parse import parse, find, node_text, span

RULE = "unsigned-sign-op"

# operators whose result depends on signed-vs-unsigned interpretation
_SIGN_OPS = {"/", "%", "<", ">", ">>"}


def _sign_of_decl(decl, src_b):
    for ann in find(decl, "marker_annotation", "annotation"):
        name = ann.child_by_field_name("name")
        if name is None:
            continue
        n = node_text(name, src_b)
        if n == "Unsigned":
            return "unsigned"
        if n == "Signed":
            return "signed"
    return None


def _build_sign_map(tree, src_b):
    """Map declared identifier name -> 'signed'/'unsigned'."""
    signs = {}
    for decl in find(
        tree.root_node,
        "formal_parameter",
        "local_variable_declaration",
        "field_declaration",
    ):
        sign = _sign_of_decl(decl, src_b)
        if sign is None:
            continue
        if decl.type == "formal_parameter":
            name = decl.child_by_field_name("name")
            if name is not None:
                signs[node_text(name, src_b)] = sign
        else:
            for vd in find(decl, "variable_declarator"):
                name = vd.child_by_field_name("name")
                if name is not None:
                    signs[node_text(name, src_b)] = sign
    return signs


def _operand_sign(node, src_b, signs):
    if node is None or node.type != "identifier":
        return None
    return signs.get(node_text(node, src_b))


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    signs = _build_sign_map(tree, src_b)
    findings = []
    for be in find(tree.root_node, "binary_expression"):
        op = be.child_by_field_name("operator")
        left = be.child_by_field_name("left")
        right = be.child_by_field_name("right")
        if op is None:
            continue
        op_t = node_text(op, src_b)
        ls = _operand_sign(left, src_b, signs)
        rs = _operand_sign(right, src_b, signs)
        line, col, _, _ = span(be)
        evidence = node_text(be, src_b)

        # mixing signed and unsigned operands is always wrong
        if ls and rs and ls != rs:
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "binary operation mixes @Signed and @Unsigned operands",
                    "note": evidence,
                    "help": "do not mix sign domains; convert one operand or use "
                    "the unsigned utility methods (Integer/Long.*Unsigned)",
                }
            )
            continue

        # sign-dependent operator applied to an unsigned operand
        if op_t in _SIGN_OPS and (ls == "unsigned" or rs == "unsigned"):
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"operator '{op_t}' interprets an @Unsigned value as signed",
                    "note": evidence,
                    "help": "use the unsigned utility methods (e.g. "
                    "Integer.divideUnsigned/remainderUnsigned/compareUnsigned, "
                    "or '>>>' for an unsigned shift)",
                }
            )
    return findings

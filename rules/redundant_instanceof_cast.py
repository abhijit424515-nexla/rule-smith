# rule: An instanceof check followed by an explicit cast to the same type should use Java 16+ pattern matching for instanceof.
# (authored by RuleSmith from the description above)

# rule: An instanceof check followed by an explicit cast to the same type should use Java 16+ pattern matching for instanceof.
"""Redundant instanceof + explicit cast to the same type that Java 16+ pattern matching would replace."""

from rulesmith.parse import parse, find, span, node_text

RULE = "redundant-instanceof-cast"


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        # instanceof checks lacking a pattern variable: (operand, type, node)
        insts = []
        for io in find(m, "instanceof_expression"):
            left = io.child_by_field_name("left")
            right = io.child_by_field_name("right")
            if left is None or right is None:
                continue
            # already pattern-matched (has binding name/pattern) -> nothing to do
            if (
                io.child_by_field_name("name") is not None
                or io.child_by_field_name("pattern") is not None
            ):
                continue
            insts.append(
                (node_text(left, src_b).strip(), node_text(right, src_b).strip(), io)
            )
        if not insts:
            continue
        # explicit casts in the same method: (value, type)
        casts = []
        for ce in find(m, "cast_expression"):
            ctype = ce.child_by_field_name("type")
            cval = ce.child_by_field_name("value")
            if ctype is None or cval is None:
                continue
            casts.append(
                (node_text(cval, src_b).strip(), node_text(ctype, src_b).strip())
            )
        for operand, typ, io in insts:
            if any(cval == operand and ctype == typ for cval, ctype in casts):
                line, col, _, _ = span(io)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"`{operand} instanceof {typ}` is paired with an explicit cast `({typ}) {operand}`",
                        "note": f"instanceof check and explicit cast both target `{operand}` as `{typ}`",
                        "help": f"use pattern matching: `if ({operand} instanceof {typ} v)` then use `v` instead of casting",
                    }
                )
    return findings

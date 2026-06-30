# rule: Every switch needs a default branch and each non-empty case must terminate (break/return/throw) unless explicitly marked fallthrough; matches over a sealed type/enum should be exhaustive rather than falling through to a throwing default.
# (authored by RuleSmith from the description above)

# rule: Every switch needs a default branch and each non-empty case must terminate (break/return/throw) unless explicitly marked fallthrough; matches over a sealed type/enum should be exhaustive rather than falling through to a throwing default.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "switch-default-and-termination"

# Statements that stop control flow leaving a case (no fallthrough).
TERMINATORS = {
    "break_statement",
    "return_statement",
    "throw_statement",
    "continue_statement",
    "yield_statement",
}


def _statements(group):
    """Body statements of an old-style case group (drop switch_label labels)."""
    return [c for c in group.named_children if c.type != "switch_label"]


def _terminates(stmt):
    if stmt.type in TERMINATORS:
        return True
    # ponytail: only unwrap a trailing block; if/else both-return etc. may
    # false-positive. Add per-branch CFG termination if it bites.
    if stmt.type == "block":
        inner = stmt.named_children
        return bool(inner) and _terminates(inner[-1])
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    fall_comments = [
        c
        for c in find(tree.root_node, "line_comment", "block_comment")
        if "fall" in node_text(c, src_bytes).lower()
    ]

    for sw in find(tree.root_node, "switch_expression"):
        body = sw.child_by_field_name("body")
        if body is None:
            continue

        # 1) missing default branch
        has_default = any(
            node_text(lbl, src_bytes).strip().startswith("default")
            for lbl in find(body, "switch_label")
        )
        if not has_default:
            line, col, _, _ = span(sw)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "switch has no default branch.",
                    "note": node_text(sw, src_bytes).splitlines()[0][:60],
                    "help": "Add a default branch; matches over an enum/sealed type should be exhaustive rather than relying on a throwing default.",
                }
            )

        # 2) non-empty old-style case that falls through to the next case
        groups = [
            c for c in body.named_children if c.type == "switch_block_statement_group"
        ]
        for i, grp in enumerate(groups):
            stmts = _statements(grp)
            if not stmts:
                continue  # empty case: stacked label, legitimate fallthrough
            if i == len(groups) - 1:
                continue  # last group falls through to switch end, harmless
            if _terminates(stmts[-1]):
                continue
            nxt = groups[i + 1]
            if any(
                grp.end_byte <= c.start_byte < nxt.start_byte for c in fall_comments
            ):
                continue  # explicitly marked fallthrough
            line, col, _, _ = span(grp)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Non-empty case falls through to the next case without break/return/throw.",
                    "note": node_text(stmts[-1], src_bytes).splitlines()[0][:60],
                    "help": "End the case with break/return/throw, or add a // fall through comment if intended.",
                }
            )

    return findings

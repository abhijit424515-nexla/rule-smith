from rulesmith.parse import parse, find, span, node_text

RULE = "no-switch-fallthrough"

# statement types that legally terminate a case group
_TERMINATORS = {
    "break_statement",
    "return_statement",
    "throw_statement",
    "continue_statement",
    "yield_statement",
}
_SKIP = {"switch_label", "comment", "line_comment", "block_comment"}


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    # colon-form groups only; arrow form ("case x ->") cannot fall through
    for group in find(tree.root_node, "switch_block_statement_group"):
        stmts = [c for c in group.named_children if c.type not in _SKIP]
        if not stmts:
            continue  # stacked labels (case 1: case 2:) -- falls to next group, allowed
        last = stmts[-1]
        # checks last statement type only; a case ending in a block
        # `{ ...; break; }` or an if/else where every branch returns is not
        # unwound. Upgrade to a CFG postdominator check if those show up.
        if last.type in _TERMINATORS:
            continue
        label = next(
            (c for c in group.named_children if c.type == "switch_label"), group
        )
        line, col, _, _ = span(label)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "switch case falls through; end it with break, return, or throw",
                "note": node_text(label, src_bytes).strip(),
                "help": "Add break/return/throw, or stack the label with the next case if intentional.",
            }
        )
    return findings

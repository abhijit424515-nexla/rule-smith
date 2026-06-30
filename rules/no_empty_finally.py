# rule: do not use an empty finally block

from rulesmith.parse import parse, find, node_text, span

RULE = "no-empty-finally"


def _block_is_empty(block):
    # A finally block is empty if it has no real statements. Comments are named
    # nodes in tree-sitter-java, so a comment-only block must still count as empty.
    for child in block.named_children:
        if "comment" not in child.type:
            return False
    return True


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for fin in find(tree.root_node, "finally_clause"):
        block = fin.child_by_field_name("body")
        if block is None:
            blocks = [c for c in fin.children if c.type == "block"]
            if not blocks:
                continue
            block = blocks[-1]
        if not _block_is_empty(block):
            continue
        line, col, _, _ = span(fin)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Do not use an empty finally block.",
                "note": node_text(fin, src_bytes),
                "help": "An empty finally block does nothing but obscure control flow. Remove it.",
            }
        )
    return findings

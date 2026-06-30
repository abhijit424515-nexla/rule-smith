# rule: control-flow nesting of if, for, while, and try must not exceed a depth of 4

from rulesmith.parse import parse, find, span, node_text

RULE = "max-control-flow-nesting"

MAX_DEPTH = 4
CONTROL = {
    "if_statement",
    "for_statement",
    "enhanced_for_statement",
    "while_statement",
    "try_statement",
}


def _is_else_if(node):
    # `else if` is parsed as an if_statement in the parent if's `alternative`
    # field. It is not real nesting, so do not count it as a deeper level.
    p = node.parent
    if p is None or node.type != "if_statement" or p.type != "if_statement":
        return False
    return p.child_by_field_name("alternative") is node


def _rec(node, depth, src_bytes, file, findings):
    cur = depth
    if node.type in CONTROL:
        if not _is_else_if(node):
            cur = depth + 1
            if cur == MAX_DEPTH + 1:
                # Report only the first level past the limit per branch so a
                # single over-nested chain counts once.
                line, col, _el, _ec = span(node)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "control-flow nesting depth %d exceeds maximum of %d"
                        % (cur, MAX_DEPTH),
                        "note": node_text(node, src_bytes).strip().splitlines()[0][:80],
                        "help": "Extract inner branches/loops into helper methods or use early returns to flatten nesting.",
                    }
                )
    for child in node.children:
        _rec(child, cur, src_bytes, file, findings)


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        _rec(method, 0, src_bytes, file, findings)
    return findings

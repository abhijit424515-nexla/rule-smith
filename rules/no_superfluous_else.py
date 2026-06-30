# rule: do not use an else branch when the if branch always returns, throws, breaks, or continues

from rulesmith.parse import parse, find, span

RULE = "no-superfluous-else"

JUMPS = {"return_statement", "throw_statement", "break_statement", "continue_statement"}


def _always_exits(node):
    """True if control never falls off the end of this statement."""
    if node is None:
        return False
    t = node.type
    if t in JUMPS:
        return True
    if t == "block":
        stmts = [c for c in node.named_children if not c.type.endswith("comment")]
        return _always_exits(stmts[-1]) if stmts else False
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    out = []
    for ifs in find(tree.root_node, "if_statement"):
        alt = ifs.child_by_field_name("alternative")
        if alt is None:
            continue
        cons = ifs.child_by_field_name("consequence")
        if not _always_exits(cons):
            continue
        line, col, _el, _ec = span(ifs)
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Superfluous 'else': the 'if' branch always exits (return/throw/break/continue).",
                "note": "consequence terminates control flow; the else block can be unindented.",
                "help": "Drop the 'else' and move its body to the same level as the 'if'.",
            }
        )
    return out

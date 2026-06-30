# rule: A loop body whose every path ends in an unconditional break/return means the loop runs at most once, usually a bug.
# (authored by RuleSmith from the description above)

# rule: A loop body whose every path ends in an unconditional break/return means the loop runs at most once, usually a bug.
"""Flag loops whose body always exits via break/return on the first iteration."""

from rulesmith.parse import parse, find, span

RULE = "loop-runs-at-most-once"

_LOOPS = ("for_statement", "enhanced_for_statement", "while_statement", "do_statement")


def _always_exits(node):
    # True if every path through `node` ends in this loop's break/return.
    if node is None:
        return False
    t = node.type
    if t in ("break_statement", "return_statement"):
        return True
    if t == "block":
        # sequential: block exits if any reachable statement always exits.
        return any(_always_exits(c) for c in node.named_children)
    if t == "if_statement":
        alt = node.child_by_field_name("alternative")
        if alt is None:
            return False  # false-branch falls through -> may loop again
        return _always_exits(node.child_by_field_name("consequence")) and _always_exits(
            alt
        )
    if t == "labeled_statement":
        return any(_always_exits(c) for c in node.named_children)
    # nested loops / switch / continue / plain statements: not a guaranteed exit
    # of THIS loop (a nested break/continue targets the inner construct).
    return False


def analyze_source(src, file="<src>"):
    tree, _src_b = parse(src)
    findings = []
    for loop in find(tree.root_node, *_LOOPS):
        body = loop.child_by_field_name("body")
        if body is None or not _always_exits(body):
            continue
        line, col, _el, _ec = span(loop)
        kind = loop.type.replace("_statement", "")
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Loop runs at most once: every path through its body ends in break/return.",
                "note": f"{kind} body has no path that reaches a next iteration",
                "help": "Drop the loop if a single check was intended, or let some path fall through/continue.",
            }
        )
    return findings

# rule: Statements the control-flow graph proves can never execute (e.g. following an unconditional return/throw/break/continue) must be removed.
# (authored by RuleSmith from the description above)

# rule: statements the control-flow graph proves can never execute (after an unconditional return/throw/break/continue) must be removed
from rulesmith.parse import parse, find, span, node_text
from rulesmith.cfg import build_method

RULE = "unreachable-code"


def _reachable(cfg):
    """Node ids reachable from ENTRY (BFS over CFG successor edges)."""
    seen = {cfg.entry.id}
    stack = [cfg.entry.id]
    while stack:
        i = stack.pop()
        for j in cfg.nodes[i].succ:
            if j not in seen:
                seen.add(j)
                stack.append(j)
    return seen


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        cfg = build_method(m, src_bytes)
        reach = _reachable(cfg)
        # any CFG node wrapping a real statement that ENTRY can't reach is dead.
        # the builder leaves stmts after return/throw/break/continue with no
        # predecessor edge, so BFS simply never visits them.
        dead = [n for n in cfg.nodes.values() if n.ts is not None and n.id not in reach]
        spans = [(n.ts.start_byte, n.ts.end_byte, n) for n in dead]
        for sb_, eb_, n in spans:
            # report the outermost dead statement of a region only: drop a node
            # whose span is strictly contained in another dead node's span.
            if any(
                o is not n and osb <= sb_ and eb_ <= oeb and (osb, oeb) != (sb_, eb_)
                for osb, oeb, o in spans
            ):
                continue
            line, col, _, _ = span(n.ts)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "unreachable statement; control flow can never reach it",
                    "note": node_text(n.ts, src_bytes).strip().splitlines()[0],
                    "help": "Remove the dead statement, or fix the control flow above it.",
                }
            )
    findings.sort(key=lambda f: (f["line"], f["col"]))
    return findings

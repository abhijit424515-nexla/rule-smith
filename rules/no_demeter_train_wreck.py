# rule: do not chain more than 3 method calls in a single expression (law of demeter train wreck)

from rulesmith.parse import parse, find, span, node_text

RULE = "no-demeter-train-wreck"

MAX_CHAIN = 3


def _chain_len(mi):
    # Count consecutive method-invocation links reached via the `object` field.
    n = 0
    cur = mi
    while cur is not None and cur.type == "method_invocation":
        n += 1
        cur = cur.child_by_field_name("object")
    return n


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for mi in find(tree.root_node, "method_invocation"):
        # Only the outermost invocation of a chain (parent is not itself a call).
        p = mi.parent
        if p is not None and p.type == "method_invocation":
            continue
        n = _chain_len(mi)
        if n <= MAX_CHAIN:
            continue
        line, col, _el, _ec = span(mi)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"method-call chain of length {n} exceeds {MAX_CHAIN}",
                "note": node_text(mi, src_bytes).strip()[:80],
                "help": "Break the chain (law of demeter): introduce intermediate "
                "variables or ask a collaborator for the result directly.",
            }
        )
    return findings

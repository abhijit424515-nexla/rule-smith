# rule: A caught InterruptedException must be rethrown or have the interrupt status restored via Thread.currentThread().interrupt(); silently swallowing it loses the cancellation signal.
# (authored by RuleSmith from the description above)

# rule: A caught InterruptedException must be rethrown or have the interrupt status restored via Thread.currentThread().interrupt(); silently swallowing it loses the cancellation signal.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "interrupted-exception-swallowed"


def _catches_interrupted(catch_node, src):
    """True if this catch clause names InterruptedException (incl. multi-catch)."""
    for param in find(catch_node, "catch_formal_parameter"):
        for t in find(param, "type_identifier", "scoped_type_identifier"):
            if node_text(t, src).strip().split(".")[-1] == "InterruptedException":
                return True
    return False


def _handled(block, src):
    """True if the catch body rethrows or restores the interrupt status."""
    # Rethrow (incl. wrapping in another throw) preserves the signal.
    if find(block, "throw_statement"):
        return True
    # Thread.currentThread().interrupt() restores the flag.
    for call in find(block, "method_invocation"):
        name = call.child_by_field_name("name")
        if name is not None and node_text(name, src) == "interrupt":
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for catch in find(tree.root_node, "catch_clause"):
        if not _catches_interrupted(catch, src_bytes):
            continue
        block = catch.child_by_field_name("body")
        if block is None:
            continue
        if _handled(block, src_bytes):
            continue
        line, col, _, _ = span(catch)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Caught InterruptedException is swallowed without rethrowing or restoring the interrupt status.",
                "note": "catch (InterruptedException ...) body has no throw and no Thread.currentThread().interrupt()",
                "help": "Rethrow the exception or call Thread.currentThread().interrupt() to preserve the cancellation signal.",
                "judge": True,
            }
        )
    return findings

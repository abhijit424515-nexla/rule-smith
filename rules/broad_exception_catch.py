# rule: Catching Throwable, Error, Exception, or RuntimeException broadly traps JVM errors and unrelated bugs that should propagate; catch the narrowest applicable type.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "broad-exception-catch"

# Catching any of these traps JVM errors / unrelated bugs that should propagate.
BROAD = {"Throwable", "Error", "Exception", "RuntimeException"}


def _caught_types(catch_node, src):
    """Return (name, node) for each type in a catch clause, incl. multi-catch unions."""
    out = []
    for param in find(catch_node, "catch_formal_parameter"):
        # catch_type holds one or more type_identifier / scoped_type_identifier nodes
        for t in find(param, "type_identifier"):
            name = node_text(t, src).strip()
            out.append((name, t))
        for t in find(param, "scoped_type_identifier"):
            # e.g. java.lang.Exception -> last segment
            name = node_text(t, src).strip().split(".")[-1]
            out.append((name, t))
    return out


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for catch in find(tree.root_node, "catch_clause"):
        for name, node in _caught_types(catch, src_bytes):
            if name in BROAD:
                line, col, _, _ = span(node)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"Catching broad type '{name}' traps JVM errors and unrelated bugs.",
                        "note": f"catch ({name} ...)",
                        "help": "Catch the narrowest applicable exception type instead.",
                    }
                )
    return findings

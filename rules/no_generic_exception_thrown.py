# rule: do not throw a raw Exception, RuntimeException, Throwable, or Error; throw a specific exception type

from rulesmith.parse import parse, find, span, node_text

RULE = "no-generic-exception-thrown"

_GENERIC = {"Exception", "RuntimeException", "Throwable", "Error"}


def analyze_source(src, file="<src>"):
    """Flag `throw new X(...)` where X is one of the over-broad built-in
    types. We look at object_creation_expression nodes that are the direct
    expression of a throw_statement, and compare the final segment of the
    instantiated type name against the disallowed set (so both `Exception`
    and `java.lang.Exception` are caught)."""
    tree, src_bytes = parse(src)
    findings = []
    for thr in find(tree.root_node, "throw_statement"):
        obj = next(
            (c for c in thr.children if c.type == "object_creation_expression"),
            None,
        )
        if obj is None:
            continue
        type_node = obj.child_by_field_name("type")
        if type_node is None:
            continue
        name = node_text(type_node, src_bytes).split(".")[-1].strip()
        if name not in _GENERIC:
            continue
        line, col, _, _ = span(thr)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Do not throw raw {name}; throw a specific exception type.",
                "note": node_text(thr, src_bytes),
                "help": "Throw a domain-specific or standard subclass "
                "(e.g. IllegalArgumentException, IllegalStateException, IOException) "
                "so callers can catch precisely.",
            }
        )
    return findings

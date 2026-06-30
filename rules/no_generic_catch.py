# rule: catch blocks must not catch generic Exception, Throwable, or Error

from rulesmith.parse import parse, find, node_text, span

RULE = "no-generic-catch"

BANNED = {"Exception", "Throwable", "Error"}


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for catch in find(tree.root_node, "catch_clause"):
        # catch_formal_parameter -> catch_type -> type_identifier(s)
        for type_id in find(catch, "type_identifier"):
            name = node_text(type_id, src_bytes)
            if name in BANNED:
                line, col, _, _ = span(type_id)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "catch block catches generic '%s'" % name,
                        "note": node_text(catch, src_bytes).splitlines()[0],
                        "help": "Catch a specific exception subclass instead of '%s'."
                        % name,
                    }
                )
    return findings

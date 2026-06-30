# rule: An exception is constructed but never thrown or assigned, so the intended error path is silently dead.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "dead-exception-construction"


def _is_exception_type(name):
    base = name.split(".")[-1].split("<")[0].strip()
    return base.endswith("Exception") or base.endswith("Error") or base == "Throwable"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for obj in find(tree.root_node, "object_creation_expression"):
        type_node = obj.child_by_field_name("type")
        if type_node is None:
            continue
        type_name = node_text(type_node, src_bytes)
        if not _is_exception_type(type_name):
            continue
        # A constructed exception whose result is the whole statement is discarded:
        # it was not thrown, assigned, returned, or passed as an argument.
        parent = obj.parent
        if parent is None or parent.type != "expression_statement":
            continue
        line, col, _, _ = span(obj)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Exception '{type_name}' is constructed but never thrown or used.",
                "note": node_text(parent, src_bytes).strip(),
                "help": "Throw it (throw new ...), assign/return it, or remove the dead construction.",
            }
        )
    return findings

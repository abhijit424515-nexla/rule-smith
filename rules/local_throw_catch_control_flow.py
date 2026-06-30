# rule: Throwing a non-error exception that is caught locally within the same method and used to direct normal control flow abuses exceptions for flow steering rather than fault signaling.
# (authored by RuleSmith from the description above)

# rule: Throwing a non-error exception that is caught locally within the same method and used to direct normal control flow abuses exceptions for flow steering rather than fault signaling.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "local-throw-catch-control-flow"

# Catching one of these makes ANY thrown exception in the try a local catch target.
BROAD = {"Exception", "RuntimeException", "Throwable"}


def _simple(name):
    return name.split(".")[-1].split("<")[0].strip()


def _caught_names(try_node, src):
    """Simple names caught by THIS try's own catch clauses (not nested tries)."""
    names = set()
    for child in try_node.children:
        if child.type != "catch_clause":
            continue
        for param in find(child, "catch_formal_parameter"):
            for t in find(param, "type_identifier"):
                names.add(node_text(t, src).strip())
            for t in find(param, "scoped_type_identifier"):
                names.add(_simple(node_text(t, src)))
    return names


def _in_nested_try(throw_node, body_node):
    p = throw_node.parent
    while p is not None and p.id != body_node.id:
        if p.type == "try_statement":
            return True
        p = p.parent
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for try_node in find(tree.root_node, "try_statement"):
        body = try_node.child_by_field_name("body")
        if body is None:
            continue
        caught = _caught_names(try_node, src_bytes)
        if not caught:
            continue
        for throw in find(body, "throw_statement"):
            if _in_nested_try(throw, body):
                continue  # belongs to an inner try's own catch
            new_expr = None
            for oce in find(throw, "object_creation_expression"):
                new_expr = oce
                break
            if new_expr is None:
                continue  # `throw e;` rethrow, not flow steering
            type_node = new_expr.child_by_field_name("type")
            if type_node is None:
                continue
            thrown = _simple(node_text(type_node, src_bytes))
            if thrown.endswith("Error"):
                continue  # genuine fault, not control flow
            if thrown not in caught and not (caught & BROAD):
                continue
            line, col, _, _ = span(throw)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": (
                        f"Exception '{thrown}' is thrown and caught locally in the same "
                        f"method, steering control flow instead of signaling a fault."
                    ),
                    "note": node_text(throw, src_bytes).strip(),
                    "help": (
                        "Use a normal control-flow construct (return, break, a flag, or a "
                        "helper method) instead of throwing an exception you catch yourself."
                    ),
                }
            )
    return findings

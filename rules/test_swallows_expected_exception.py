# rule: A test that invokes code expected to throw inside a try block but omits fail()/assertThrows after the call passes silently when no exception is raised.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "test-swallows-expected-exception"


def _is_test_method(method, src_b):
    name = method.child_by_field_name("name")
    if name is not None and node_text(name, src_b).startswith("test"):
        return True
    for ann in find(method, "annotation", "marker_annotation"):
        if "Test" in node_text(ann, src_b):
            return True
    return False


def _try_body(try_node):
    # try_statement = `try` block catch_clause* finally_clause?;
    # the try body is the first direct `block` child.
    for c in try_node.children:
        if c.type == "block":
            return c
    return None


def _has_fail_call(body, src_b):
    for call in find(body, "method_invocation"):
        name = call.child_by_field_name("name")
        if name is not None and node_text(name, src_b) in ("fail", "assertThrows"):
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for method in find(tree.root_node, "method_declaration"):
        if not _is_test_method(method, src_b):
            continue
        for try_node in find(method, "try_statement"):
            if not find(try_node, "catch_clause"):
                continue
            body = _try_body(try_node)
            if body is None:
                continue
            # need an actual call (the code expected to throw) inside the try
            if not find(body, "method_invocation"):
                continue
            if _has_fail_call(body, src_b):
                continue
            line, col, _, _ = span(try_node)
            out.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "try/catch in test expects an exception but never calls fail()/assertThrows after the throwing call",
                    "note": node_text(try_node, src_b)[:200],
                    "help": "Add fail(...) as the last statement in the try block, or replace the try/catch with assertThrows.",
                }
            )
    return out

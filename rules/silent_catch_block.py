# rule: A catch block that neither rethrows, wraps, logs meaningfully, nor takes recovery action silently hides failures and lets the method continue with invalid state.
# (authored by RuleSmith from the description above)

# rule: A catch block that neither rethrows, wraps, logs meaningfully, nor takes recovery action silently hides failures and lets the method continue with invalid state.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "silent-catch-block"

# Node types whose presence in a catch body counts as "handling": rethrow/wrap,
# logging or any recovery action (a call), or control-flow recovery.
_HANDLES = (
    "throw_statement",
    "method_invocation",
    "return_statement",
    "break_statement",
    "continue_statement",
    "assignment_expression",
)


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    out = []
    for cc in find(tree.root_node, "catch_clause"):
        body = cc.child_by_field_name("body")
        if body is None:
            continue
        # ponytail: a nested try's throw/log counts as handling the outer catch
        # too. Acceptable; refine with CFG if nested handlers prove noisy.
        if find(body, *_HANDLES):
            continue
        param = cc.child_by_field_name("parameter")
        name = node_text(param, sb) if param is not None else "exception"
        line, col, _, _ = span(cc)
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Catch block for '{name}' swallows the exception: it does not "
                f"rethrow, wrap, log, or take any recovery action.",
                "note": node_text(cc, sb),
                "help": "Rethrow or wrap the exception, log it meaningfully, or take a "
                "concrete recovery action so the failure is not hidden.",
            }
        )
    return out

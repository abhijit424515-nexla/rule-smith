# rule: Dropping the returned handle of a Stream terminal/intermediate op or a CompletableFuture/ExecutorService.submit loses results and silently swallows exceptions.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, node_text, span

RULE = "dropped-async-stream-result"

# Ops whose return value carries the result/exception. Dropping it as a bare
# statement loses data and silently swallows failures.
STREAM_OPS = {
    "map",
    "mapToInt",
    "mapToLong",
    "mapToObj",
    "mapToDouble",
    "filter",
    "sorted",
    "distinct",
    "limit",
    "skip",
    "peek",
    "flatMap",
    "collect",
    "count",
    "reduce",
    "sum",
    "average",
    "min",
    "max",
    "findFirst",
    "findAny",
    "anyMatch",
    "allMatch",
    "noneMatch",
    "toList",
}
FUTURE_OPS = {
    "submit",  # ExecutorService.submit -> Future (swallows thrown exceptions)
    "supplyAsync",
    "runAsync",
    "thenApply",
    "thenApplyAsync",
    "thenCompose",
    "thenComposeAsync",
    "thenCombine",
    "handle",
    "exceptionally",
    "whenComplete",
}
FLAGGED = STREAM_OPS | FUTURE_OPS


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for call in find(tree.root_node, "method_invocation"):
        # only the OUTERMOST call in a chain: its result is what gets dropped.
        if call.parent is None or call.parent.type != "expression_statement":
            continue
        name = call.child_by_field_name("name")
        if name is None:
            continue
        op = node_text(name, sb)
        if op not in FLAGGED:
            continue
        line, col = span(call)[0], span(call)[1]
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Return value of '%s' is dropped; result is lost and exceptions are silently swallowed."
                % op,
                "note": node_text(call, sb).strip(),
                "help": "Assign, return, or otherwise consume the handle (e.g. block on the Future, collect the Stream).",
            }
        )
    return findings

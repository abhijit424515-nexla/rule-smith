# rule: Use OptionalInt/OptionalLong/OptionalDouble instead of Optional<Integer>/Optional<Long>/Optional<Double> to avoid boxing.
# (authored by RuleSmith from the description above)

# rule: Use OptionalInt/OptionalLong/OptionalDouble instead of Optional<Integer>/Optional<Long>/Optional<Double> to avoid boxing.
"""Optional<Integer/Long/Double> boxes a primitive; use OptionalInt/OptionalLong/OptionalDouble."""

from rulesmith.parse import parse, find, span, node_text

RULE = "optional-of-boxed-primitive"

_BOXED = {"Integer": "OptionalInt", "Long": "OptionalLong", "Double": "OptionalDouble"}


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    seen = set()
    # A generic_type is `Base<Args>`; named children = [base, type_arguments].
    for gt in find(tree.root_node, "generic_type"):
        kids = list(gt.named_children)
        if len(kids) < 2:
            continue
        base = kids[0]
        targs = kids[-1]
        if targs.type != "type_arguments":
            continue
        # strip any qualifier, e.g. java.util.Optional -> Optional
        base_name = node_text(base, src_b).split(".")[-1]
        if base_name != "Optional":
            continue
        arg_names = [node_text(a, src_b) for a in targs.named_children]
        if len(arg_names) != 1:
            continue
        boxed = arg_names[0]
        repl = _BOXED.get(boxed)
        if not repl:
            continue
        line, col = span(gt)[0], span(gt)[1]
        key = (line, col)
        if key in seen:  # dedup: one finding per occurrence span
            continue
        seen.add(key)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Optional<{boxed}> boxes a primitive; use {repl}.",
                "note": f"generic_type Optional<{boxed}> at {file}:{line}:{col}",
                "help": f"Replace Optional<{boxed}> with {repl} to avoid boxing.",
            }
        )
    return findings

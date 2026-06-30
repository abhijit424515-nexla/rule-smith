# rule: Flag two or more consecutive parameters of identical type where transposing arguments compiles silently; distinct wrapper/value types prevent swaps.
# (authored by RuleSmith from the description above)

# rule: Flag two or more consecutive parameters of identical type where transposing arguments compiles silently; distinct wrapper/value types prevent swaps.

from rulesmith.parse import parse, find, span, node_text

RULE = "adjacent-same-type-positional-params"


def _norm(t):
    # collapse whitespace so "List < String >" == "List<String>"
    return "".join(t.split())


def analyze_source(src, file="<src>"):
    findings = []
    tree, src_bytes = parse(src)

    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        params = method.child_by_field_name("parameters")
        if params is None:
            continue
        # only real positional params; spread_parameter (varargs) is not swappable here
        formals = [c for c in params.children if c.type == "formal_parameter"]
        typed = []
        for p in formals:
            tnode = p.child_by_field_name("type")
            if tnode is None:
                continue
            typed.append((_norm(node_text(tnode, src_bytes)), p))
        if len(typed) < 2:
            continue

        # walk maximal runs of consecutive identical types
        i = 0
        n = len(typed)
        while i < n:
            j = i + 1
            while j < n and typed[j][0] == typed[i][0]:
                j += 1
            run_len = j - i
            if run_len >= 2:
                tname = typed[i][0]
                first_p = typed[i][1]
                line, col, _, _ = span(first_p)
                names = [
                    node_text(typed[k][1].child_by_field_name("name"), src_bytes)
                    for k in range(i, j)
                    if typed[k][1].child_by_field_name("name") is not None
                ]
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"{run_len} consecutive parameters of identical type '{tname}'; transposed arguments compile silently",
                        "note": ", ".join(names),
                        "help": "Reorder so adjacent params differ in type, or introduce distinct wrapper/value types so a swap fails to compile",
                    }
                )
            i = j

    return findings

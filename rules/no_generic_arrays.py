# rule: Do not mix arrays with generics: generic array creation and arrays of parameterized types are unsafe; prefer List.
# (authored by RuleSmith from the description above)

# rule: Do not mix arrays with generics: generic array creation and arrays of parameterized types are unsafe; prefer List.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "no-generic-arrays"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = {}

    def add(node):
        line, col, _, _ = span(node)
        if line in findings:
            return
        findings[line] = {
            "rule": RULE,
            "file": file,
            "line": line,
            "col": col,
            "message": "Do not mix arrays with generics; prefer List.",
            "note": node_text(node, src_bytes).strip()[:120],
            "help": "Generic array creation and arrays of parameterized types are unsafe. Use a List<T> (e.g. List<List<String>>) instead of T<...>[].",
        }

    # generic array creation: new T<...>[...]
    for ac in find(tree.root_node, "array_creation_expression"):
        t = ac.child_by_field_name("type")
        if t is not None and t.type == "generic_type":
            add(ac)

    # arrays of parameterized types: T<...>[]
    for at in find(tree.root_node, "array_type"):
        el = at.child_by_field_name("element")
        if el is not None and el.type == "generic_type":
            add(at)

    return list(findings.values())

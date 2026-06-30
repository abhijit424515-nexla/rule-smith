# rule: A method that accesses fields/getters of one other class more often than members of its own class belongs on the envied class.
# (authored by RuleSmith from the description above)

# rule: a method that accesses fields/getters of one other class more often than members of its own class belongs on the envied class

from rulesmith.parse import parse, find, span, node_text

RULE = "feature-envy"


def _receiver(node, src_bytes):
    """Return the receiver identifier text for an access, or None for own/this/unclassifiable."""
    obj = node.child_by_field_name("object")
    if obj is None:
        return None  # implicit this -> own
    if obj.type != "identifier":
        return None  # chained call, field_access chain, etc. -> skip
    text = node_text(obj, src_bytes)
    if text == "this":
        return None
    if text and text[0].isupper():
        return None  # ClassName.staticCall / Math.max / System.out -> skip
    return text


def analyze_source(src, file="<src>"):
    findings = []
    tree, src_bytes = parse(src)

    for method in find(tree.root_node, "method_declaration"):
        own = 0
        foreign = {}
        for acc in find(method, "method_invocation", "field_access"):
            rcv = _receiver(acc, src_bytes)
            if rcv is None:
                obj = acc.child_by_field_name("object")
                if obj is None or (
                    obj.type == "identifier" and node_text(obj, src_bytes) == "this"
                ):
                    own += 1
                continue
            foreign[rcv] = foreign.get(rcv, 0) + 1

        if not foreign:
            continue
        envied, count = max(foreign.items(), key=lambda kv: kv[1])
        # envy: one foreign object accessed more than own members, and at least twice
        if count > own and count >= 2:
            line, col, _, _ = span(method)
            name_node = method.child_by_field_name("name")
            mname = node_text(name_node, src_bytes) if name_node else "<method>"
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"Method '{mname}' accesses '{envied}' more than its own class; consider moving it onto '{envied}'",
                    "note": f"{count} accesses of '{envied}' vs {own} own-class members",
                    "help": f"Move '{mname}' (or the envious logic) onto the '{envied}' type",
                    "judge": True,
                }
            )

    return findings

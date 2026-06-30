# rule: Iterator.hasNext() must be side-effect free and must not call next(); next() must throw NoSuchElementException when exhausted.
# (authored by RuleSmith from the description above)

# rule: Iterator.hasNext() must be side-effect free and must not call next(); next() must throw NoSuchElementException when exhausted.
"""Iterator contract: hasNext() must not call next() (side-effect free); next() must throw NoSuchElementException."""

from rulesmith.parse import parse, find, span, node_text

RULE = "iterator-contract-violation"


def _name(method, src_b):
    n = method.child_by_field_name("name")
    return node_text(n, src_b) if n else ""


def _arity(method):
    params = method.child_by_field_name("parameters")
    if params is None:
        return 0
    return len([c for c in params.children if c.type == "formal_parameter"])


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    methods = find(tree.root_node, "method_declaration")
    names = {_name(m, src_b) for m in methods}

    # Only treat as an iterator if the class exposes both hasNext and next.
    if not ({"hasNext", "next"} <= names):
        return findings

    for m in methods:
        name = _name(m, src_b)
        body = m.child_by_field_name("body")
        if body is None:
            continue

        if name == "hasNext" and _arity(m) == 0:
            for inv in find(body, "method_invocation"):
                callee = inv.child_by_field_name("name")
                if callee is None or node_text(callee, src_b) != "next":
                    continue
                obj = inv.child_by_field_name("object")
                if obj is not None and node_text(obj, src_b) != "this":
                    continue
                line, col, *_ = span(inv)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "hasNext() calls next(); hasNext() must be side-effect free",
                        "note": node_text(inv, src_b),
                        "help": "hasNext() must only test for a next element, never consume it. Move advancement into next().",
                    }
                )

        elif name == "next" and _arity(m) == 0:
            if "NoSuchElementException" not in node_text(body, src_b):
                line, col, *_ = span(m.child_by_field_name("name"))
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "next() never references NoSuchElementException; it must throw it when exhausted",
                        "note": node_text(m.child_by_field_name("name"), src_b),
                        "help": "Guard next() with `if (!hasNext()) throw new NoSuchElementException();`.",
                    }
                )

    return findings

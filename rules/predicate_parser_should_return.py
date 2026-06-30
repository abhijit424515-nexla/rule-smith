# rule: Flag validate*/check*/isValid methods returning void or boolean whose only effect is throwing or signaling; a parser should return the refined type so the proven invariant flows downstream.
# (authored by RuleSmith from the description above)

# rule: validate*/check*/isValid methods returning void or boolean whose only effect is throwing or signaling should return the refined type so the proven invariant flows downstream

from rulesmith.parse import parse, find, node_text, span

RULE = "predicate-parser-should-return"

# Returns/throws nested in these belong to an inner function, not this method.
_SCOPE = {"lambda_expression", "method_declaration", "constructor_declaration"}


def _name_signals_validation(name):
    n = name.lower()
    return n.startswith("validate") or n.startswith("check") or n.startswith("isvalid")


def _base_type(type_node, src_bytes):
    if type_node is None:
        return None
    return node_text(type_node, src_bytes).split("<", 1)[0].strip().split(".")[-1]


def _owned_by(node, body):
    # True if node lives inside a nested lambda/method within body.
    n = node.parent
    while n is not None and n != body:
        if n.type in _SCOPE:
            return True
        n = n.parent
    return False


def _direct(nodes, body):
    return [n for n in nodes if not _owned_by(n, body)]


def _return_value(ret):
    kids = ret.named_children
    return kids[0] if kids else None


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        name_node = m.child_by_field_name("name")
        if name_node is None or not _name_signals_validation(
            node_text(name_node, src_bytes)
        ):
            continue
        ret = _base_type(m.child_by_field_name("type"), src_bytes)
        if ret not in ("void", "boolean", "Boolean"):
            continue
        body = m.child_by_field_name("body")
        if body is None:
            continue

        throws = _direct(find(body, "throw_statement"), body)
        returns = _direct(find(body, "return_statement"), body)

        if ret == "void":
            # void validator: only effect is throwing.
            signals = bool(throws)
        else:
            # boolean validator: only effect is signaling valid/invalid.
            valued = [r for r in returns if _return_value(r) is not None]
            literal_only = bool(valued) and all(
                _return_value(r).type in ("true", "false") for r in valued
            )
            signals = literal_only or bool(throws)
        if not signals:
            continue

        line, col, _, _ = span(name_node)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Predicate-style '{node_text(name_node, src_bytes)}' only throws/signals; return the refined type instead.",
                "note": node_text(name_node, src_bytes) + " -> " + (ret or "?"),
                "help": "Make the parser return the validated/refined value (e.g. the parsed object or Optional) so the proven invariant flows downstream, per 'parse, don't validate'.",
            }
        )
    return findings

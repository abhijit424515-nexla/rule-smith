# rule: A fluent builder's terminal method (e.g. build()) must only be invoked after all required setter calls have occurred on that receiver.
# (authored by RuleSmith from the description above)

# rule: A fluent builder's terminal method (e.g. build()) must only be invoked after all required setter calls have occurred on that receiver.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "builder-terminal-before-setters"

# Terminal methods that finalize a fluent builder. No-arg by convention.
_TERMINAL = {"build", "create", "buildPartial"}


def _recv_name(inv, src):
    """If invocation's receiver is a plain identifier, return its text."""
    obj = inv.child_by_field_name("object")
    if obj is None or obj.type != "identifier":
        return None
    return node_text(obj, src)


def _calls_on(method, recv, src):
    """[(name, invocation)] for method_invocations whose object is identifier `recv`."""
    out = []
    for inv in find(method, "method_invocation"):
        if _recv_name(inv, src) != recv:
            continue
        nm = inv.child_by_field_name("name")
        if nm is None:
            continue
        out.append((node_text(nm, src), inv))
    return out


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        # ponytail: keyed on receiver identifier; does not track reassignment of
        # the variable to a fresh builder after build(). Add liveness via cfg if
        # that false-positive shows up in practice.
        for inv in find(method, "method_invocation"):
            nm = inv.child_by_field_name("name")
            if nm is None or node_text(nm, src_bytes) not in _TERMINAL:
                continue
            recv = _recv_name(inv, src_bytes)
            if recv is None:  # fluent chain (build() on an expression) -> ok
                continue
            build_pos = inv.start_byte
            late = [
                (n, i)
                for (n, i) in _calls_on(method, recv, src_bytes)
                if n not in _TERMINAL and i.start_byte > build_pos
            ]
            if not late:
                continue
            line, col, _, _ = span(inv)
            n0, i0 = late[0]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Builder '%s' is finalized by '%s()' before setter '%s()' runs on it."
                    % (recv, node_text(nm, src_bytes), n0),
                    "note": node_text(i0, src_bytes)[:200],
                    "help": "Move all setter calls before the terminal %s() call."
                    % node_text(nm, src_bytes),
                }
            )
    return findings

# rule: The ??? placeholder (or equivalent TODO-throwing stub) compiles but throws NotImplementedError at runtime, leaking partial-by-design stubs into shipped code paths.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "todo-throwing-stub"

# markers that mark a throw as a partial-by-design stub, not a real error
_MARKERS = (
    "todo",
    "fixme",
    "not implemented",
    "notimplemented",
    "unimplemented",
    "not yet implemented",
    "implement me",
)
# bare throw of one of these as a method's sole statement == ??? placeholder
_STUB_EXC = ("UnsupportedOperationException", "NotImplementedError")


def _type_name(obj_creation, src):
    t = obj_creation.child_by_field_name("type")
    return node_text(t, src) if t is not None else ""


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        body = method.child_by_field_name("body")
        if body is None:
            continue
        stmt_count = sum(1 for c in body.named_children if c.type != "comment")
        for th in find(method, "throw_statement"):
            ocs = find(th, "object_creation_expression")
            if not ocs:
                continue
            oc = ocs[0]
            short = _type_name(oc, src_bytes).split(".")[-1]
            args = oc.child_by_field_name("arguments")
            arg_named = list(args.named_children) if args is not None else []
            msg = " ".join(node_text(a, src_bytes) for a in arg_named).lower()
            is_marker = any(m in msg for m in _MARKERS)
            is_bare_stub = short in _STUB_EXC and stmt_count == 1 and not arg_named
            if is_marker or is_bare_stub:
                line, col, _, _ = span(th)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": "TODO-throwing stub leaks into a shipped code path",
                        "note": node_text(th, src_bytes),
                        "help": "Implement the method or remove the placeholder stub before shipping.",
                    }
                )
    return findings

# rule: A method annotated or declared pure (@Pure, @SideEffectFree) must not assign to non-local state, mutate fields/arguments, perform IO, or call a known-impure method.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "pure-method-no-side-effects"

# Annotations that declare a method side-effect-free.
PURE_ANNOTATIONS = {"Pure", "SideEffectFree"}

# Method names that perform IO regardless of receiver.
IO_NAMES = {
    "println",
    "print",
    "printf",
    "write",
    "flush",
    "read",
    "readLine",
    "newLine",
}

# Receivers whose calls are inherently IO.
IO_OBJECTS = {"System.out", "System.err"}

# Names that mutate their receiver (collections, builders, ...).
MUTATOR_NAMES = {
    "add",
    "addAll",
    "put",
    "putAll",
    "set",
    "remove",
    "removeAll",
    "clear",
    "push",
    "pop",
    "offer",
    "poll",
    "append",
}


def _annotation_names(method, src):
    """Simple-name set of annotations on the method's modifiers."""
    names = set()
    mods = None
    for c in method.children:
        if c.type == "modifiers":
            mods = c
            break
    if mods is None:
        return names
    for ann in find(mods, "marker_annotation", "annotation"):
        name = ann.child_by_field_name("name")
        if name is not None:
            names.add(node_text(name, src).split(".")[-1])
    return names


def _mk(file, line, col, message, note, tag):
    return {
        "rule": RULE,
        "file": file,
        "line": line,
        "col": col,
        "message": message,
        "note": note,
        "help": f"Remove side effects from {tag} methods, or drop the purity annotation.",
    }


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration"):
        anns = _annotation_names(method, src_bytes)
        pure = anns & PURE_ANNOTATIONS
        if not pure:
            continue
        body = method.child_by_field_name("body")
        if body is None:
            continue
        tag = "@" + sorted(pure)[0]

        # Assignment to non-local state: this.x = ... / obj.x = ... / arr[i] = ...
        for asg in find(body, "assignment_expression"):
            left = asg.child_by_field_name("left")
            if left is not None and left.type in ("field_access", "array_access"):
                line, col, _, _ = span(asg)
                findings.append(
                    _mk(
                        file,
                        line,
                        col,
                        "pure method assigns to non-local state",
                        node_text(asg, src_bytes),
                        tag,
                    )
                )

        # In-place mutation via ++/-- on a field or array element.
        for upd in find(body, "update_expression"):
            for ch in upd.children:
                if ch.type in ("field_access", "array_access"):
                    line, col, _, _ = span(upd)
                    findings.append(
                        _mk(
                            file,
                            line,
                            col,
                            "pure method mutates state via increment/decrement",
                            node_text(upd, src_bytes),
                            tag,
                        )
                    )
                    break

        # IO and known-impure (mutating) calls.
        for call in find(body, "method_invocation"):
            name_n = call.child_by_field_name("name")
            obj_n = call.child_by_field_name("object")
            name = node_text(name_n, src_bytes) if name_n is not None else ""
            obj = node_text(obj_n, src_bytes) if obj_n is not None else ""
            line, col, _, _ = span(call)
            if obj in IO_OBJECTS or name in IO_NAMES:
                findings.append(
                    _mk(
                        file,
                        line,
                        col,
                        "pure method performs IO",
                        node_text(call, src_bytes),
                        tag,
                    )
                )
            elif obj and name in MUTATOR_NAMES:
                findings.append(
                    _mk(
                        file,
                        line,
                        col,
                        "pure method calls a known-impure (mutating) method",
                        node_text(call, src_bytes),
                        tag,
                    )
                )

    return findings

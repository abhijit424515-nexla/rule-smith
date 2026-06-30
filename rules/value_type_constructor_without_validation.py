# rule: For a value/wrapper type, flag a public constructor with no validation when the invariant should be enforced by a validating smart constructor or factory.
# (authored by RuleSmith from the description above)

# rule: For a value/wrapper type, flag a public constructor with no validation when the invariant should be enforced by a validating smart constructor or factory.
"""Flag public constructors of immutable value types that enforce no invariant."""

from rulesmith.parse import parse, find, span, node_text

RULE = "value-type-constructor-without-validation"

# names that signal a precondition check inside the constructor
VALIDATION_NAMES = {
    "requireNonNull",
    "checkArgument",
    "checkNotNull",
    "checkState",
    "isTrue",
    "notNull",
    "hasText",
    "state",
    "validate",
    "verify",
}


def _modifiers_text(node, src_b):
    for ch in node.children:
        if ch.type == "modifiers":
            return node_text(ch, src_b)
    return ""


def _instance_field_counts(class_body, src_b):
    total = finals = 0
    for fd in class_body.children:
        if fd.type != "field_declaration":
            continue
        mods = _modifiers_text(fd, src_b).split()
        if "static" in mods:
            continue
        total += 1
        if "final" in mods:
            finals += 1
    return total, finals


def _has_validation(body, src_b):
    # any branch/throw/ternary = a guard; any known check call = validation
    if find(
        body,
        "if_statement",
        "throw_statement",
        "conditional_expression",
        "switch_expression",
        "switch_statement",
    ):
        return True
    for mi in find(body, "method_invocation"):
        name = mi.child_by_field_name("name")
        if name is not None and node_text(name, src_b) in VALIDATION_NAMES:
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for cls in find(tree.root_node, "class_declaration"):
        body = cls.child_by_field_name("body")
        if body is None:
            continue
        total, finals = _instance_field_counts(body, src_b)
        # immutable value type heuristic: >=1 field, all instance fields final
        if total == 0 or finals != total:
            continue
        name_node = cls.child_by_field_name("name")
        cls_name = node_text(name_node, src_b) if name_node else "<anon>"
        for ctor in body.children:
            if ctor.type != "constructor_declaration":
                continue
            if "public" not in _modifiers_text(ctor, src_b).split():
                continue
            params = ctor.child_by_field_name("parameters")
            if params is None or not find(params, "formal_parameter"):
                continue  # no args, no invariant to enforce
            cbody = ctor.child_by_field_name("body")
            if cbody is None or _has_validation(cbody, src_b):
                continue
            line, col, *_ = span(ctor)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"public constructor of value type '{cls_name}' performs no validation",
                    "note": "all instance fields are final (immutable value type) but the constructor enforces no invariant",
                    "help": "make the constructor private and expose a validating static factory (e.g. of(...)), or add precondition checks",
                    "judge": True,
                }
            )
    return findings

# rule: Optional should only be a return type; flag Optional used for fields, collection elements, or method/constructor parameters.
# (authored by RuleSmith from the description above)

# rule: Optional should only be a return type; flag Optional used for fields, collection elements, or method/constructor parameters.
"""Optional as field/parameter/collection-element check (Optional belongs in return types only)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "optional-as-field-or-parameter"

# java.util Optional family; matched on the bare type name (no type resolution).
OPTIONAL_NAMES = {"Optional", "OptionalInt", "OptionalLong", "OptionalDouble"}


def _bare_name(text):
    # strip generics + package qualifier: "java.util.Optional<String>" -> "Optional"
    return text.split("<", 1)[0].split(".")[-1].strip()


def _is_optional_type(node, src_b):
    if node is None:
        return False
    if node.type in ("generic_type", "type_identifier", "scoped_type_identifier"):
        return _bare_name(node_text(node, src_b)) in OPTIONAL_NAMES
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node
    findings = []
    seen = set()

    def add(node, why, help_):
        line, col, _, _ = span(node)
        key = (line, col, why)
        if key in seen:
            return
        seen.add(key)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Optional used as {why}; Optional should only be a return type.",
                "note": node_text(node, src_b).strip(),
                "help": help_,
            }
        )

    # fields
    for fd in find(root, "field_declaration"):
        t = fd.child_by_field_name("type")
        if _is_optional_type(t, src_b):
            add(
                t,
                "a field type",
                "Store a plain (null-checked) reference; don't hold Optional in a field.",
            )

    # method / constructor parameters
    for fp in find(root, "formal_parameter"):
        t = fp.child_by_field_name("type")
        if _is_optional_type(t, src_b):
            add(
                fp,
                "a parameter type",
                "Take a plain parameter (overload or accept null); don't pass Optional in.",
            )

    # collection elements: Optional appearing as a type argument (e.g. List<Optional<X>>)
    for ta in find(root, "type_arguments"):
        for child in ta.named_children:
            if _is_optional_type(child, src_b):
                add(
                    child,
                    "a collection element / type argument",
                    "Don't nest Optional inside a collection; use the plain element type.",
                )

    return findings

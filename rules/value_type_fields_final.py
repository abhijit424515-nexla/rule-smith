# rule: Non-final instance fields in classes used as value/data types (records, case-class-like POJOs) should be final so the type is immutable by default.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "value-type-fields-final"

# A class is treated as a value/data type if its name carries a data-ish suffix
# or it is annotated like one (Lombok @Value/@Data, JSR-305 @Immutable, etc.).
# Records are deliberately ignored: their components are already final.
VALUE_SUFFIXES = (
    "Dto",
    "DTO",
    "Data",
    "Value",
    "Pojo",
    "POJO",
    "Vo",
    "VO",
    "Record",
    "Event",
    "Message",
)
VALUE_ANNOTATIONS = ("@Value", "@Data", "@Immutable")


def _modifiers_text(node, src_bytes):
    for c in node.children:
        if c.type == "modifiers":
            return node_text(c, src_bytes)
    return ""


def _modifier_keywords(node):
    for c in node.children:
        if c.type == "modifiers":
            return {k.type for k in c.children}
    return set()


def _is_value_type(class_node, src_bytes):
    name_node = class_node.child_by_field_name("name")
    name = node_text(name_node, src_bytes) if name_node else ""
    mods = _modifiers_text(class_node, src_bytes)
    if any(a in mods for a in VALUE_ANNOTATIONS):
        return True
    return any(name.endswith(s) for s in VALUE_SUFFIXES)


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for class_node in find(tree.root_node, "class_declaration"):
        if not _is_value_type(class_node, src_bytes):
            continue
        body = class_node.child_by_field_name("body")
        if body is None:
            continue
        cname_node = class_node.child_by_field_name("name")
        cname = node_text(cname_node, src_bytes) if cname_node else "?"
        # Only direct members of this class body; nested classes get their own pass.
        for member in body.children:
            if member.type != "field_declaration":
                continue
            keywords = _modifier_keywords(member)
            if "static" in keywords or "final" in keywords:
                continue
            decl = member.child_by_field_name("declarator")
            fname = "?"
            if decl is not None:
                n = decl.child_by_field_name("name")
                if n is not None:
                    fname = node_text(n, src_bytes)
            line, col, _, _ = span(member)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"Non-final instance field '{fname}' in value/data type '{cname}'",
                    "note": node_text(member, src_bytes),
                    "help": "Mark the field 'final' so the value type is immutable by default.",
                }
            )
    return findings

# rule: do not build a string with += concatenation inside a loop; use a StringBuilder

from rulesmith.parse import parse, find, span, node_text

RULE = "no-string-concat-in-loop"

LOOP_TYPES = {
    "for_statement",
    "enhanced_for_statement",
    "while_statement",
    "do_statement",
}
STRING_TYPES = {"String", "CharSequence"}
# ponytail: method-scope String tracking, not full type inference; upgrade if field/qualified-type concats matter


def _string_vars(method, src_bytes):
    names = set()
    for decl in find(method, "local_variable_declaration", "formal_parameter"):
        t = decl.child_by_field_name("type")
        if t is None or node_text(t, src_bytes) not in STRING_TYPES:
            continue
        if decl.type == "formal_parameter":
            n = decl.child_by_field_name("name")
            if n is not None:
                names.add(node_text(n, src_bytes))
        else:
            for vd in find(decl, "variable_declarator"):
                n = vd.child_by_field_name("name")
                if n is not None:
                    names.add(node_text(n, src_bytes))
    return names


def _in_loop(node, method):
    p = node.parent
    while p is not None and p.id != method.id:
        if p.type in LOOP_TYPES:
            return True
        p = p.parent
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        svars = _string_vars(method, src_bytes)
        if not svars:
            continue
        for asn in find(method, "assignment_expression"):
            op = asn.child_by_field_name("operator")
            left = asn.child_by_field_name("left")
            if op is None or left is None:
                continue
            if node_text(op, src_bytes) != "+=":
                continue
            if left.type != "identifier" or node_text(left, src_bytes) not in svars:
                continue
            if not _in_loop(asn, method):
                continue
            line, col, _, _ = span(asn)
            name = node_text(left, src_bytes)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "String built with '+=' inside a loop; use a StringBuilder",
                    "note": node_text(asn, src_bytes),
                    "help": "Replace '%s += ...' in the loop with a StringBuilder and call .append(), then %s = sb.toString() after the loop."
                    % (name, name),
                }
            )
    return findings

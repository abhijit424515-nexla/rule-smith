# rule: static final constant field names must be in UPPER_SNAKE_CASE

from rulesmith.parse import parse, find, node_text, span

RULE = "static-final-constant-upper-snake"


def _is_upper_snake(name):
    # UPPER_SNAKE_CASE: only A-Z, 0-9, underscore; at least one letter;
    # equal to its own upper-case form; no leading/trailing underscore.
    if not name:
        return False
    if name[0] == "_" or name[-1] == "_":
        return False
    if not all(c.isalnum() or c == "_" for c in name):
        return False
    if not any(c.isalpha() for c in name):
        return False
    return name == name.upper()


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for fd in find(tree.root_node, "field_declaration"):
        mods = [m for m in fd.children if m.type == "modifiers"]
        if not mods:
            continue
        mod_text = node_text(mods[0], src_bytes)
        if "static" not in mod_text.split() or "final" not in mod_text.split():
            continue
        for decl in find(fd, "variable_declarator"):
            name_node = decl.child_by_field_name("name")
            if name_node is None:
                continue
            name = node_text(name_node, src_bytes)
            if _is_upper_snake(name):
                continue
            line, col, _, _ = span(name_node)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "static final constant '%s' is not in UPPER_SNAKE_CASE"
                    % name,
                    "note": "declared with modifiers: %s" % mod_text,
                    "help": "rename '%s' to UPPER_SNAKE_CASE (e.g. %s)"
                    % (name, name.upper()),
                }
            )
    return findings

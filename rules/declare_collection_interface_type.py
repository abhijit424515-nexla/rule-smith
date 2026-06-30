# rule: do not declare a local variable or field with type ArrayList, HashMap, or HashSet; declare the interface type List, Map, or Set

from rulesmith.parse import parse, find, node_text, span

RULE = "declare-collection-interface-type"

# Concrete implementation type -> interface it should be declared as.
_CONCRETE = {"ArrayList": "List", "HashMap": "Map", "HashSet": "Set"}


def _base_name(type_node, src_bytes):
    if type_node is None:
        return None
    # ArrayList<String> -> generic_type; strip generics + package qualifier.
    base = node_text(type_node, src_bytes).split("<", 1)[0].strip()
    return base.split(".")[-1]


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for decl in find(tree.root_node, "local_variable_declaration", "field_declaration"):
        tnode = decl.child_by_field_name("type")
        base = _base_name(tnode, src_bytes)
        iface = _CONCRETE.get(base)
        if iface is None:
            continue
        line, col, _, _ = span(tnode)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Declare the interface type {iface}, not the concrete {base}.",
                "note": node_text(decl, src_bytes),
                "help": f"Change the declared type to {iface}; you can still assign new {base}<>() to it.",
            }
        )
    return findings

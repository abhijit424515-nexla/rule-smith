# rule: Flag use of mutable collection types (scala.collection.mutable, or exposing ArrayList/HashMap as API types) where an immutable type satisfies the usage.
# (authored by RuleSmith from the description above)

# rule: do not expose mutable collection types (scala.collection.mutable, or concrete ArrayList/HashMap/HashSet) as method return or parameter types where an immutable interface type satisfies the usage

from rulesmith.parse import parse, find, node_text, span

RULE = "expose-mutable-collection-type"

# Concrete mutable implementation -> immutable/interface type that usually satisfies API usage.
_CONCRETE = {
    "ArrayList": "List",
    "LinkedList": "List",
    "HashMap": "Map",
    "LinkedHashMap": "Map",
    "TreeMap": "Map",
    "HashSet": "Set",
    "LinkedHashSet": "Set",
    "TreeSet": "Set",
}


def _classify(type_node, src_bytes):
    """Return (concrete_name, suggested) if type is a flagged mutable collection, else None."""
    if type_node is None:
        return None
    text = node_text(type_node, src_bytes).strip()
    # scala.collection.mutable.Buffer<Int> -> strip generics, keep qualifier.
    qualified = text.split("<", 1)[0].strip()
    if "scala.collection.mutable." in qualified or qualified.startswith("mutable."):
        return (qualified, "an immutable scala.collection type")
    base = qualified.split(".")[-1]
    iface = _CONCRETE.get(base)
    if iface is not None:
        return (base, iface)
    return None


def _is_private(method_node, src_bytes):
    for child in method_node.children:
        if child.type == "modifiers":
            return "private" in node_text(child, src_bytes).split()
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration"):
        if _is_private(method, src_bytes):
            continue
        # Return type.
        targets = []
        rtype = method.child_by_field_name("type")
        if rtype is not None:
            targets.append(("return type", rtype))
        # Parameter types.
        params = method.child_by_field_name("parameters")
        if params is not None:
            for p in find(params, "formal_parameter", "spread_parameter"):
                ptype = p.child_by_field_name("type")
                if ptype is not None:
                    targets.append(("parameter", ptype))
        for where, tnode in targets:
            res = _classify(tnode, src_bytes)
            if res is None:
                continue
            concrete, suggested = res
            line, col, _, _ = span(tnode)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"Do not expose mutable {concrete} as a {where}; use {suggested}.",
                    "note": node_text(method, src_bytes).split("{", 1)[0].strip(),
                    "help": f"Change the {where} to {suggested}; build with {concrete} internally if needed.",
                }
            )
    return findings

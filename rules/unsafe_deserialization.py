# rule: Flag ObjectInputStream.readObject or XMLDecoder.readObject on untrusted streams with no ObjectInputFilter or resolveClass allowlist, enabling gadget-chain RCE.
# (authored by RuleSmith from the description above)

# rule: Flag ObjectInputStream.readObject or XMLDecoder.readObject on untrusted streams with no ObjectInputFilter or resolveClass allowlist, enabling gadget-chain RCE.
"""Unsafe deserialization: readObject without an ObjectInputFilter/resolveClass allowlist."""

from rulesmith.parse import parse, find, span, node_text

RULE = "unsafe-deserialization"

_SINK_TYPES = ("ObjectInputStream", "XMLDecoder")


def _sink_decl_vars(tree, src_b):
    """varname -> declared type text, for locals/fields typed as a sink stream."""
    types = {}
    for decl in find(tree.root_node, "local_variable_declaration", "field_declaration"):
        tnode = decl.child_by_field_name("type")
        if tnode is None:
            continue
        ttext = node_text(tnode, src_b)
        if not any(s in ttext for s in _SINK_TYPES):
            continue
        for d in find(decl, "variable_declarator"):
            nnode = d.child_by_field_name("name")
            if nnode is not None:
                types[node_text(nnode, src_b)] = ttext
    return types


def _object_sink_type(obj, src_b, sink_vars):
    """Return the sink type name if obj is a sink stream, else None."""
    if obj is None:
        return None
    # new ObjectInputStream(in).readObject()
    if obj.type == "object_creation_expression":
        tnode = obj.child_by_field_name("type")
        ttext = node_text(tnode, src_b) if tnode is not None else ""
        for s in _SINK_TYPES:
            if s in ttext:
                return s
        return None
    # ois.readObject() where ois is a sink-typed var
    if obj.type == "identifier":
        ttext = sink_vars.get(node_text(obj, src_b))
        if ttext:
            for s in _SINK_TYPES:
                if s in ttext:
                    return s
    return None


def _mitigated(tree, src_b):
    """True if the file installs an allowlist: setObjectInputFilter call,
    a resolveClass override, or any reference to ObjectInputFilter."""
    for inv in find(tree.root_node, "method_invocation"):
        n = inv.child_by_field_name("name")
        if n is not None and node_text(n, src_b) == "setObjectInputFilter":
            return True
    for m in find(tree.root_node, "method_declaration"):
        n = m.child_by_field_name("name")
        if n is not None and node_text(n, src_b) == "resolveClass":
            return True
    for t in find(tree.root_node, "type_identifier"):
        if node_text(t, src_b) == "ObjectInputFilter":
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    if _mitigated(tree, src_b):
        return []
    sink_vars = _sink_decl_vars(tree, src_b)
    out = []
    for inv in find(tree.root_node, "method_invocation"):
        name = inv.child_by_field_name("name")
        if name is None or node_text(name, src_b) != "readObject":
            continue
        sink = _object_sink_type(inv.child_by_field_name("object"), src_b, sink_vars)
        if sink is None:
            continue
        line, col, _, _ = span(inv)
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"{sink}.readObject() on an untrusted stream with no deserialization allowlist",
                "note": f"no ObjectInputFilter/resolveClass guard found in this file for `{node_text(inv, src_b)}`",
                "help": "install an ObjectInputFilter (setObjectInputFilter / ObjectInputFilter.Config.createFilter) or override resolveClass to allowlist expected classes",
                "judge": True,
            }
        )
    return out

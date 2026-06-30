# rule: A method that overrides a supertype or interface method should carry @Override so signature drift becomes a compile error.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "missing-override-annotation"


def _type_name(node, src):
    n = node.child_by_field_name("name")
    return node_text(n, src) if n is not None else None


def _parents(node, src):
    """Direct supertype/interface names declared in this file."""
    names = set()
    for c in node.children:
        if c.type in ("superclass", "super_interfaces", "extends_interfaces"):
            for t in find(c, "type_identifier"):
                names.add(node_text(t, src))
    return names


def _has_override(method, src):
    for ch in method.children:
        if ch.type == "modifiers":
            for a in find(ch, "marker_annotation", "annotation"):
                an = a.child_by_field_name("name")
                if an is not None and node_text(an, src) == "Override":
                    return True
    return False


def _methods(node, src):
    """Direct (non-nested) method members as (name, arity, node, has_override)."""
    body = node.child_by_field_name("body")
    out = []
    if body is None:
        return out
    for m in body.children:
        if m.type != "method_declaration":
            continue
        nm = m.child_by_field_name("name")
        if nm is None:
            continue
        params = m.child_by_field_name("parameters")
        arity = 0
        if params is not None:
            arity = sum(
                1
                for p in params.children
                if p.type in ("formal_parameter", "spread_parameter")
            )
        out.append((node_text(nm, src), arity, m, _has_override(m, src)))
    return out


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    types = {}
    for t in find(
        tree.root_node,
        "class_declaration",
        "interface_declaration",
        "enum_declaration",
    ):
        name = _type_name(t, sb)
        if name is None:
            continue
        types[name] = {"parents": _parents(t, sb), "methods": _methods(t, sb)}

    def ancestor_sigs(name, seen):
        sigs = set()
        for p in types.get(name, {}).get("parents", ()):
            if p in seen:
                continue
            seen.add(p)
            pt = types.get(p)
            if pt is not None:
                for mn, ar, _m, _o in pt["methods"]:
                    sigs.add((mn, ar))
                sigs |= ancestor_sigs(p, seen)
        return sigs

    findings = []
    for name, info in types.items():
        sigs = ancestor_sigs(name, set())
        for mn, ar, m, has_override in info["methods"]:
            if has_override:
                continue
            if (mn, ar) in sigs:
                ln, col, _, _ = span(m)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": ln,
                        "col": col,
                        "message": "Method '%s' overrides a supertype method but lacks @Override."
                        % mn,
                        "note": "%s.%s/%d matches an ancestor declaration in this file"
                        % (name, mn, ar),
                        "help": "Add @Override so signature drift becomes a compile error.",
                    }
                )
    findings.sort(key=lambda f: (f["line"], f["col"]))
    return findings

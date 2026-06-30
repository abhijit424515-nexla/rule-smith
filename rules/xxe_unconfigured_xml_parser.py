# rule: Flag DocumentBuilderFactory/SAXParserFactory/TransformerFactory/XMLInputFactory used to parse input without disabling DTDs and external entities.
# (authored by RuleSmith from the description above)

# rule: Flag DocumentBuilderFactory/SAXParserFactory/TransformerFactory/XMLInputFactory used to parse input without disabling DTDs and external entities.
"""XXE: XML parser factory created without disabling DTDs/external entities."""

from rulesmith.parse import parse, find, span, node_text

RULE = "xxe-unconfigured-xml-parser"

# factory classes whose default config is XXE-vulnerable
FACTORIES = {
    "DocumentBuilderFactory",
    "SAXParserFactory",
    "TransformerFactory",
    "XMLInputFactory",
}

# any of these calls on the factory var counts as a hardening attempt
HARDEN = {
    "setFeature",
    "setProperty",
    "setAttribute",
    "setExpandEntityReferences",
    "setXIncludeAware",
    "setExternalParameterEntities",
}


def _short(type_text):
    # type may be qualified (javax.xml.parsers.DocumentBuilderFactory)
    return type_text.split(".")[-1].strip()


def analyze_source(src, file="<src>"):
    tree, b = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        # collect factory vars that receive a hardening call in this method
        hardened = set()
        for inv in find(m, "method_invocation"):
            name = inv.child_by_field_name("name")
            obj = inv.child_by_field_name("object")
            if name is None or obj is None:
                continue
            if node_text(name, b) in HARDEN:
                hardened.add(node_text(obj, b))
        # flag each factory declaration with no hardening call on its var
        for decl in find(m, "local_variable_declaration"):
            typ = decl.child_by_field_name("type")
            if typ is None:
                continue
            tname = _short(node_text(typ, b))
            if tname not in FACTORIES:
                continue
            for d in find(decl, "variable_declarator"):
                nm = d.child_by_field_name("name")
                if nm is None:
                    continue
                vname = node_text(nm, b)
                if vname in hardened:
                    continue
                line, col, _, _ = span(nm)
                findings.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"{tname} '{vname}' parses XML without disabling DTDs/external entities (XXE risk).",
                        "note": f"no hardening call (setFeature/setProperty/setAttribute/...) on '{vname}' in this method",
                        "help": 'disable DTDs, e.g. setFeature("http://apache.org/xml/features/disallow-doctype-decl", true), enable XMLConstants.FEATURE_SECURE_PROCESSING, or set XMLInputFactory.SUPPORT_DTD=false and IS_SUPPORTING_EXTERNAL_ENTITIES=false.',
                        "judge": True,
                    }
                )
    return findings

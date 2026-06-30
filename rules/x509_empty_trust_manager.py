# rule: an X509TrustManager whose checkServerTrusted or checkClientTrusted method body is empty disables certificate validation

from rulesmith.parse import parse, find, span, node_text

RULE = "x509-empty-trust-manager"

TARGET = {"checkServerTrusted", "checkClientTrusted"}


def _enclosing_type(node):
    """Nearest class_declaration or anonymous-class object_creation_expression."""
    p = node.parent
    while p is not None:
        if p.type in ("class_declaration", "object_creation_expression"):
            return p
        p = p.parent
    return None


def _is_trust_manager(node, src):
    if node.type == "object_creation_expression":
        t = node.child_by_field_name("type")
        return t is not None and "X509TrustManager" in node_text(t, src)
    for ch in node.children:
        if ch.type in ("superclass", "super_interfaces"):
            if "X509TrustManager" in node_text(ch, src):
                return True
    return False


def _body_empty(body):
    # block with no statements; comments do not count as logic
    if body is None or body.type != "block":
        return False
    for ch in body.named_children:
        if "comment" not in ch.type:
            return False
    return True


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        name_node = m.child_by_field_name("name")
        if name_node is None:
            continue
        name = node_text(name_node, src_bytes)
        if name not in TARGET:
            continue
        owner = _enclosing_type(m)
        if owner is None or not _is_trust_manager(owner, src_bytes):
            continue
        if not _body_empty(m.child_by_field_name("body")):
            continue
        line, col, _, _ = span(name_node)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Empty {name} disables X.509 certificate validation",
                "note": node_text(m, src_bytes)[:200],
                "help": "Validate the certificate chain or throw CertificateException; never leave the trust-check body empty.",
            }
        )
    return findings

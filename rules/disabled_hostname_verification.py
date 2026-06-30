# rule: Flag use of NoopHostnameVerifier, ALLOW_ALL_HOSTNAME_VERIFIER, or a HostnameVerifier whose verify() unconditionally returns true.
# (authored by RuleSmith from the description above)

# rule: Flag use of NoopHostnameVerifier, ALLOW_ALL_HOSTNAME_VERIFIER, or a HostnameVerifier whose verify() unconditionally returns true.
"""Disabled hostname verification accepts any certificate's host, enabling MITM."""

from rulesmith.parse import parse, find, node_text, span

RULE = "disabled-hostname-verification"

_BAD_NAMES = {"NoopHostnameVerifier", "ALLOW_ALL_HOSTNAME_VERIFIER"}


def _under_import(node):
    n = node.parent
    while n is not None:
        if n.type == "import_declaration":
            return True
        n = n.parent
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    seen = set()

    # 1) known insecure verifier names (skip import lines)
    for ident in find(tree.root_node, "identifier"):
        if node_text(ident, src_b) in _BAD_NAMES and not _under_import(ident):
            line, col, _, _ = span(ident)
            key = (line, col)
            if key in seen:
                continue
            seen.add(key)
            name = node_text(ident, src_b)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"insecure hostname verifier {name} accepts any host",
                    "note": f"reference to {name}",
                    "help": "use the default HostnameVerifier or one that validates the hostname",
                }
            )

    # 2) a verify() method that unconditionally returns true
    for m in find(tree.root_node, "method_declaration"):
        nm = m.child_by_field_name("name")
        if nm is None or node_text(nm, src_b) != "verify":
            continue
        body = m.child_by_field_name("body")
        if body is None:
            continue
        # unconditional: exactly one return, value true, no branching
        rets = find(body, "return_statement")
        branches = find(
            body,
            "if_statement",
            "while_statement",
            "for_statement",
            "switch_expression",
            "ternary_expression",
        )
        if len(rets) != 1 or branches:
            continue
        rtext = node_text(rets[0], src_b).strip().rstrip(";").strip()
        if rtext != "return true":
            continue
        line, col, _, _ = span(m)
        key = (line, col)
        if key in seen:
            continue
        seen.add(key)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "HostnameVerifier.verify() unconditionally returns true",
                "note": "verify() body is `return true;` with no hostname check",
                "help": "validate the hostname against the certificate, or remove the override",
            }
        )

    return findings

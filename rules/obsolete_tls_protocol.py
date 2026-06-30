# rule: Flag SSLContext.getInstance with SSLv2/SSLv3/TLSv1.0/TLSv1.1 instead of TLSv1.2 or higher.
# (authored by RuleSmith from the description above)

# rule: Flag SSLContext.getInstance with SSLv2/SSLv3/TLSv1.0/TLSv1.1 instead of TLSv1.2 or higher.
"""Flag obsolete TLS/SSL protocols passed to SSLContext.getInstance."""

from rulesmith.parse import parse, find, span, node_text

RULE = "obsolete-tls-protocol"

# protocol string -> normalized lowercase form we reject
_OBSOLETE = {"ssl", "sslv2", "sslv3", "tls", "tlsv1", "tlsv1.0", "tlsv1.1"}


def _strip(lit):
    # node_text of a string_literal includes the surrounding quotes
    return lit[1:-1] if len(lit) >= 2 and lit[0] in "\"'" else lit


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for call in find(tree.root_node, "method_invocation"):
        name = call.child_by_field_name("name")
        obj = call.child_by_field_name("object")
        args = call.child_by_field_name("arguments")
        if name is None or args is None:
            continue
        if node_text(name, src_b) != "getInstance":
            continue
        # object must reference SSLContext (handles SSLContext, javax.net.ssl.SSLContext)
        if obj is None or not node_text(obj, src_b).split(".")[-1] == "SSLContext":
            continue
        lits = find(args, "string_literal")
        if not lits:
            continue
        proto = _strip(node_text(lits[0], src_b)).strip()
        if proto.lower() not in _OBSOLETE:
            continue
        line, col, _, _ = span(call)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f'SSLContext.getInstance("{proto}") uses an obsolete protocol',
                "note": f'protocol string "{proto}" is broken/deprecated',
                "help": 'use "TLSv1.2", "TLSv1.3", or "TLS" with an explicitly configured minimum',
            }
        )
    return findings

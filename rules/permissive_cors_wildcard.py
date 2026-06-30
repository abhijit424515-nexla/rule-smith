# rule: Flag CORS configuration setting Access-Control-Allow-Origin to the wildcard, especially combined with allow-credentials.
# (authored by RuleSmith from the description above)

# rule: Flag CORS configuration setting Access-Control-Allow-Origin to the wildcard, especially combined with allow-credentials.
"""CORS Access-Control-Allow-Origin set to '*' (worse with allow-credentials)."""

from rulesmith.parse import parse, find, span, node_text

RULE = "permissive-cors-wildcard"

# Spring/JAX-RS builder methods that set the allowed origin(s).
ORIGIN_METHODS = {
    "allowedOrigins",
    "addAllowedOrigin",
    "setAllowedOrigins",
    "allowedOriginPatterns",
    "addAllowedOriginPattern",
    "setAllowedOriginPatterns",
}
# Header writers: response.setHeader("Access-Control-Allow-Origin", "*") etc.
HEADER_METHODS = {"setHeader", "addHeader", "header", "set", "put", "add"}
CREDENTIAL_METHODS = {"allowCredentials", "setAllowCredentials"}


def _str_args(node, src_b):
    """Unquoted text of every string_literal under node."""
    out = []
    for s in find(node, "string_literal"):
        t = node_text(s, src_b)
        if len(t) >= 2 and t[0] in "\"'":
            t = t[1:-1]
        out.append(t)
    return out


def _credentials_enabled(root, src_b):
    for inv in find(root, "method_invocation"):
        nm = inv.child_by_field_name("name")
        args = inv.child_by_field_name("arguments")
        if nm is None or args is None:
            continue
        name = node_text(nm, src_b)
        atext = node_text(args, src_b)
        if name in CREDENTIAL_METHODS and "true" in atext:
            return True
        # header form: setHeader("Access-Control-Allow-Credentials", "true")
        if name in HEADER_METHODS:
            sa = _str_args(args, src_b)
            if "Access-Control-Allow-Credentials" in sa and "true" in sa:
                return True
    # @CrossOrigin(allowCredentials = "true")
    for ann in find(root, "annotation"):
        nm = ann.child_by_field_name("name")
        if nm is None or node_text(nm, src_b) != "CrossOrigin":
            continue
        if "allowCredentials" in node_text(ann, src_b) and "true" in node_text(
            ann, src_b
        ):
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node
    creds = _credentials_enabled(root, src_b)
    seen = set()
    findings = []

    def emit(node, evidence):
        line, col, _, _ = span(node)
        if (line, col) in seen:
            return
        seen.add((line, col))
        sev = (
            " combined with allow-credentials (reflected wildcard sends cookies cross-origin)"
            if creds
            else ""
        )
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "CORS allows any origin ('*')" + sev,
                "note": evidence,
                "help": "Replace the wildcard with an explicit allowlist of trusted origins; never pair '*' with allow-credentials.",
                "judge": True,
            }
        )

    for inv in find(root, "method_invocation"):
        nm = inv.child_by_field_name("name")
        args = inv.child_by_field_name("arguments")
        if nm is None or args is None:
            continue
        name = node_text(nm, src_b)
        sa = _str_args(args, src_b)
        if name in ORIGIN_METHODS and "*" in sa:
            emit(inv, f"{name}(...) passes wildcard origin '*'")
        elif (
            name in HEADER_METHODS and "Access-Control-Allow-Origin" in sa and "*" in sa
        ):
            emit(inv, f"{name}(...) sets Access-Control-Allow-Origin: *")

    # @CrossOrigin with no origins attribute defaults to allowing all origins;
    # @CrossOrigin(origins = "*") is explicit. Either is a wildcard.
    for ann in find(root, "annotation", "marker_annotation"):
        nm = ann.child_by_field_name("name")
        if nm is None or node_text(nm, src_b) != "CrossOrigin":
            continue
        atext = node_text(ann, src_b)
        has_origin_attr = "origins" in atext or "value" in atext
        if (not has_origin_attr) or '"*"' in atext:
            emit(ann, "@CrossOrigin allows all origins (wildcard / default)")

    return findings

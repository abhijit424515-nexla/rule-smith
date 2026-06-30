# rule: Flag java.util.Random/Math.random() used to generate keys, tokens, IVs, salts, session IDs, or passwords; require java.security.SecureRandom.
# (authored by RuleSmith from the description above)

# rule: Flag java.util.Random/Math.random() used to generate keys, tokens, IVs, salts, session IDs, or passwords; require java.security.SecureRandom.
"""Insecure Random (java.util.Random / Math.random) for security-sensitive values; require SecureRandom."""

from rulesmith.parse import parse, find, span, node_text

RULE = "insecure-random-for-security"

SEC_WORDS = (
    "key",
    "token",
    "iv",
    "salt",
    "session",
    "password",
    "passwd",
    "secret",
    "nonce",
    "otp",
    "apikey",
    "credential",
)


def _is_security_name(name):
    n = name.lower()
    return any(w in n for w in SEC_WORDS)


def _insecure_random_nodes(root, src_b):
    """method_invocation Math.random() and `new Random(...)` object creations."""
    hits = []
    for mi in find(root, "method_invocation"):
        obj = mi.child_by_field_name("object")
        nm = mi.child_by_field_name("name")
        if (
            nm
            and node_text(nm, src_b) == "random"
            and obj
            and node_text(obj, src_b) == "Math"
        ):
            hits.append(mi)
    for oc in find(root, "object_creation_expression"):
        t = oc.child_by_field_name("type")
        if not t:
            continue
        base = node_text(t, src_b).split("<")[0].strip().split(".")[-1]
        if base == "Random":  # excludes SecureRandom
            hits.append(oc)
    return hits


def _security_context(node, src_b):
    """Climb ancestors; return the security-relevant name if one encloses the call."""
    cur = node.parent
    while cur is not None:
        t = cur.type
        if t == "variable_declarator":
            nm = cur.child_by_field_name("name")
            if nm and _is_security_name(node_text(nm, src_b)):
                return node_text(nm, src_b)
        elif t == "assignment_expression":
            lhs = cur.child_by_field_name("left")
            if lhs and _is_security_name(node_text(lhs, src_b)):
                return node_text(lhs, src_b)
        elif t in ("method_declaration", "constructor_declaration"):
            nm = cur.child_by_field_name("name")
            if nm and _is_security_name(node_text(nm, src_b)):
                return node_text(nm, src_b)
            return None  # stop at the enclosing method boundary
        cur = cur.parent
    return None


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    seen = set()
    for rn in _insecure_random_nodes(tree.root_node, src_b):
        ctx = _security_context(rn, src_b)
        if not ctx:
            continue
        lno, c, _el, _ec = span(rn)
        if (lno, c) in seen:
            continue
        seen.add((lno, c))
        out.append(
            {
                "rule": RULE,
                "file": file,
                "line": lno,
                "col": c,
                "message": f"insecure RNG for security-sensitive value '{ctx}'",
                "note": node_text(rn, src_b),
                "help": "use java.security.SecureRandom for keys, tokens, IVs, salts, session IDs, or passwords",
            }
        )
    return out

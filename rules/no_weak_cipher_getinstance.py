# rule: do not call Cipher.getInstance with a weak algorithm or mode such as DES, RC4, or ECB

from rulesmith.parse import parse, find, span, node_text

RULE = "no-weak-cipher-getinstance"

# Weak algorithms (matched as the algorithm token) and weak modes (matched as the mode token).
WEAK_ALGS = {"DES", "DESEDE", "RC4", "ARCFOUR", "RC2", "BLOWFISH"}
WEAK_MODES = {"ECB"}


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for call in find(tree.root_node, "method_invocation"):
        name = call.child_by_field_name("name")
        if name is None or node_text(name, src_bytes) != "getInstance":
            continue
        obj = call.child_by_field_name("object")
        if obj is None or not node_text(obj, src_bytes).endswith("Cipher"):
            continue
        args = call.child_by_field_name("arguments")
        if args is None:
            continue
        lit = next((a for a in args.children if a.type == "string_literal"), None)
        if lit is None:
            continue
        # strip surrounding quotes from the literal text
        raw = node_text(lit, src_bytes).strip('"')
        parts = [p.strip().upper() for p in raw.split("/")]
        alg = parts[0] if parts else ""
        mode = parts[1] if len(parts) > 1 else ""
        bad = []
        if alg in WEAK_ALGS:
            bad.append("algorithm " + alg)
        if mode in WEAK_MODES:
            bad.append("mode " + mode)
        if not bad:
            continue
        line, col, _, _ = span(call)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Cipher.getInstance uses a weak " + " and ".join(bad),
                "note": 'transform="' + raw + '"',
                "help": "Use a strong algorithm and authenticated mode, e.g. AES/GCM/NoPadding.",
            }
        )
    return findings

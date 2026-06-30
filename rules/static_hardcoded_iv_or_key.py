# rule: Flag IvParameterSpec/GCMParameterSpec or SecretKeySpec constructed from a constant byte array or string literal rather than a randomly generated IV or key.
# (authored by RuleSmith from the description above)

# rule: Flag IvParameterSpec/GCMParameterSpec or SecretKeySpec constructed from a constant byte array or string literal rather than a randomly generated IV or key.
"""Hardcoded IV/key passed to IvParameterSpec/GCMParameterSpec/SecretKeySpec."""

from rulesmith.parse import parse, find, span, node_text

RULE = "static-hardcoded-iv-or-key"

TARGET = {"IvParameterSpec", "GCMParameterSpec", "SecretKeySpec"}
_DECODE = {"decode", "parseHexBinary", "decodeHex", "fromHexString"}


def _resolve(ident, src_b, method_ts):
    """Last-resort: value expression bound to a local var name in this method."""
    name = node_text(ident, src_b)
    val = None
    for decl in find(method_ts, "local_variable_declaration"):
        for d in find(decl, "variable_declarator"):
            n = d.child_by_field_name("name")
            if n is not None and node_text(n, src_b) == name:
                val = d.child_by_field_name("value")
    return val


def _is_constant(node, src_b, method_ts, depth=0):
    """True if node is a compile-time-constant IV/key source (literal bytes/string)."""
    if node is None or depth > 6:
        return False
    t = node.type
    if t == "string_literal":
        return True
    if t == "array_initializer":
        return True
    if t == "array_creation_expression":
        # new byte[]{...} is constant; new byte[16] (random-filled later) is not.
        return bool(find(node, "array_initializer"))
    if t == "method_invocation":
        obj = node.child_by_field_name("object")
        if obj is not None and _is_constant(obj, src_b, method_ts, depth + 1):
            return True  # "literal".getBytes()
        mname_node = node.child_by_field_name("name")
        mname = node_text(mname_node, src_b) if mname_node is not None else ""
        if mname in _DECODE:
            args = node.child_by_field_name("arguments")
            if args is not None:
                for a in args.named_children:
                    if _is_constant(a, src_b, method_ts, depth + 1):
                        return True  # Base64.decode("const"), hex decode, etc.
        return False
    if t == "identifier":
        return _is_constant(
            _resolve(node, src_b, method_ts), src_b, method_ts, depth + 1
        )
    if t in ("parenthesized_expression", "cast_expression"):
        for c in node.named_children:
            if _is_constant(c, src_b, method_ts, depth + 1):
                return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        for oce in find(m, "object_creation_expression"):
            tnode = oce.child_by_field_name("type")
            if tnode is None:
                continue
            tname = node_text(tnode, src_b).split(".")[-1]
            if tname not in TARGET:
                continue
            args = oce.child_by_field_name("arguments")
            if args is None:
                continue
            argv = list(args.named_children)
            # The byte payload: IvParameterSpec/SecretKeySpec -> arg 0; GCMParameterSpec -> arg 1
            # (arg 0 there is the tag length int). Skip trailing algorithm-name string args.
            idx = 1 if tname == "GCMParameterSpec" else 0
            if idx >= len(argv):
                continue
            payload = argv[idx]
            if not _is_constant(payload, src_b, m):
                continue
            line, col, _, _ = span(oce)
            kind = "key material" if tname == "SecretKeySpec" else "IV/nonce"
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"{tname} built from a hardcoded constant rather than randomly generated {kind}",
                    "note": f"argument: {node_text(payload, src_b)[:60]}",
                    "help": "Generate the IV/key at runtime (SecureRandom.nextBytes / KeyGenerator) and never embed it in source.",
                }
            )
    return findings

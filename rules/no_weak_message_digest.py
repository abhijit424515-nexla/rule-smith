# rule: do not call MessageDigest.getInstance with a weak algorithm MD5, SHA-1, or SHA1

from rulesmith.parse import parse, find, node_text

RULE = "no-weak-message-digest"

WEAK = {"MD5", "SHA-1", "SHA1"}


def _arg_text(arg, src):
    # string_literal text includes surrounding quotes; strip them
    t = node_text(arg, src)
    if len(t) >= 2 and t[0] in "\"'" and t[-1] == t[0]:
        return t[1:-1]
    return t


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for call in find(tree.root_node, "method_invocation"):
        name = call.child_by_field_name("name")
        obj = call.child_by_field_name("object")
        args = call.child_by_field_name("arguments")
        if name is None or obj is None or args is None:
            continue
        if node_text(name, src_bytes) != "getInstance":
            continue
        if node_text(obj, src_bytes) != "MessageDigest":
            continue
        # first positional argument
        arg_nodes = [c for c in args.named_children]
        if not arg_nodes:
            continue
        first = arg_nodes[0]
        if first.type != "string_literal":
            continue
        algo = _arg_text(first, src_bytes)
        if algo.strip().upper() in WEAK:
            line = first.start_point[0] + 1
            col = first.start_point[1] + 1
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Weak hash algorithm '%s' passed to MessageDigest.getInstance"
                    % algo,
                    "note": node_text(call, src_bytes),
                    "help": "Use a strong algorithm such as SHA-256 or SHA-512.",
                }
            )
    return findings

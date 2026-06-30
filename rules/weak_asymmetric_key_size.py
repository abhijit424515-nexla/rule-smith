# rule: Flag KeyPairGenerator/KeyGenerator initialized with insecure key sizes (RSA/DSA below 2048, EC below 224).
# (authored by RuleSmith from the description above)

# rule: Flag KeyPairGenerator/KeyGenerator initialized with insecure key sizes (RSA/DSA below 2048, EC below 224).
"""Weak asymmetric key size passed to a key generator's initialize/init."""

from rulesmith.parse import parse, find, span, node_text

RULE = "weak-asymmetric-key-size"


def _canon_threshold(algo):
    a = algo.upper()
    if a.startswith("EC"):
        return "EC", 224
    if a.startswith("RSA"):
        return "RSA", 2048
    if a.startswith("DSA"):
        return "DSA", 2048
    return None, None


def _int_value(node, src_b):
    txt = node_text(node, src_b).replace("_", "")
    try:
        return int(txt, 0)
    except ValueError:
        return None


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node
    findings = []
    for method in find(root, "method_declaration", "constructor_declaration"):
        # var name -> algorithm string, from KeyPairGenerator/KeyGenerator.getInstance("...")
        var_algo = {}
        for decl in find(method, "local_variable_declaration"):
            algo = None
            for inv in find(decl, "method_invocation"):
                name = inv.child_by_field_name("name")
                obj = inv.child_by_field_name("object")
                if name is None or obj is None:
                    continue
                if node_text(name, src_b) != "getInstance":
                    continue
                if node_text(obj, src_b) not in ("KeyPairGenerator", "KeyGenerator"):
                    continue
                args = inv.child_by_field_name("arguments")
                if args is None:
                    continue
                for s in find(args, "string_literal"):
                    algo = node_text(s, src_b).strip('"')
                    break
                break
            if algo is None:
                continue
            for vd in find(decl, "variable_declarator"):
                vn = vd.child_by_field_name("name")
                if vn is not None:
                    var_algo[node_text(vn, src_b)] = algo

        # find initialize/init calls on those vars
        for inv in find(method, "method_invocation"):
            name = inv.child_by_field_name("name")
            obj = inv.child_by_field_name("object")
            if name is None or obj is None:
                continue
            if node_text(name, src_b) not in ("initialize", "init"):
                continue
            algo = var_algo.get(node_text(obj, src_b))
            if algo is None:
                continue
            canon, thresh = _canon_threshold(algo)
            if canon is None:
                continue
            args = inv.child_by_field_name("arguments")
            if args is None:
                continue
            size = None
            for lit in find(args, "decimal_integer_literal"):
                size = _int_value(lit, src_b)
                break
            if size is None or size >= thresh:
                continue
            line, col, _, _ = span(inv)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"{canon} key size {size} is below the secure minimum {thresh}",
                    "note": f"{node_text(obj, src_b)}.{node_text(name, src_b)}({size}) on a {algo} generator",
                    "help": f"Use at least {thresh} bits for {canon} keys",
                }
            )
    return findings

# rule: Flag File/Paths/FileInputStream constructed from tainted input reaching the filesystem without canonicalization and base-directory containment check.
# (authored by RuleSmith from the description above)

# rule: Flag File/Paths/FileInputStream constructed from tainted input reaching the filesystem without canonicalization and base-directory containment check.
# (authored by RuleSmith from the description above)
"""Path traversal: filesystem sink fed tainted input with no canonicalize+containment guard."""

from rulesmith.parse import parse, find, span, node_text

RULE = "path-traversal-file-access"

# request/stream readers that return attacker-controlled data
_TAINT_SRC = {
    "getParameter",
    "getParameterValues",
    "getParameterMap",
    "getHeader",
    "getHeaders",
    "getQueryString",
    "getRequestURI",
    "getRequestURL",
    "getPathInfo",
    "getPathTranslated",
    "getInputStream",
    "getReader",
    "getCookies",
    "readLine",
    "nextLine",
}
_SINK_TYPES = {
    "File",
    "FileInputStream",
    "FileOutputStream",
    "FileReader",
    "FileWriter",
    "RandomAccessFile",
}
_FILES_METHODS = {
    "newInputStream",
    "newOutputStream",
    "newBufferedReader",
    "newBufferedWriter",
    "readAllBytes",
    "readString",
    "readAllLines",
    "lines",
    "newByteChannel",
    "copy",
    "write",
}
_CANON = {"getCanonicalPath", "getCanonicalFile", "toRealPath"}


def _invocations(node):
    res = []
    if node.type == "method_invocation":
        res.append(node)
    res.extend(find(node, "method_invocation"))
    return res


def _idents(node):
    if node.type == "identifier":
        return [node]
    return find(node, "identifier")


def _has_source(node, src_b):
    for inv in _invocations(node):
        n = inv.child_by_field_name("name")
        if n is not None and node_text(n, src_b) in _TAINT_SRC:
            return True
    return False


def _refs_tainted(node, src_b, tainted):
    for i in _idents(node):
        if node_text(i, src_b) in tainted:
            return True
    return False


def _tainted_vars(method, src_b):
    """Names assigned (directly or transitively) from a taint source."""
    assigns = []  # (target_name, value_node)
    for decl in find(method, "local_variable_declaration"):
        for d in find(decl, "variable_declarator"):
            name = d.child_by_field_name("name")
            val = d.child_by_field_name("value")
            if name is not None and val is not None:
                assigns.append((node_text(name, src_b), val))
    for asn in find(method, "assignment_expression"):
        left = asn.child_by_field_name("left")
        right = asn.child_by_field_name("right")
        if left is not None and left.type == "identifier" and right is not None:
            assigns.append((node_text(left, src_b), right))
    tainted = set()
    changed = True
    while changed:
        changed = False
        for name, val in assigns:
            if name in tainted:
                continue
            if _has_source(val, src_b) or _refs_tainted(val, src_b, tainted):
                tainted.add(name)
                changed = True
    return tainted


def _mitigated(method, src_b):
    has_canon = has_contain = False
    for inv in find(method, "method_invocation"):
        n = inv.child_by_field_name("name")
        if n is None:
            continue
        t = node_text(n, src_b)
        if t in _CANON:
            has_canon = True
        if t == "startsWith":
            has_contain = True
    return has_canon and has_contain


def _is_sink(node, src_b):
    """Return (label, args_node) if node is a filesystem sink, else None."""
    if node.type == "object_creation_expression":
        tnode = node.child_by_field_name("type")
        ttext = node_text(tnode, src_b) if tnode is not None else ""
        if any(s == ttext or ttext.endswith("." + s) for s in _SINK_TYPES):
            return "new " + ttext, node.child_by_field_name("arguments")
    if node.type == "method_invocation":
        obj = node.child_by_field_name("object")
        nm = node.child_by_field_name("name")
        if obj is None or nm is None:
            return None
        otext, ntext = node_text(obj, src_b), node_text(nm, src_b)
        if otext == "Paths" and ntext == "get":
            return "Paths.get", node.child_by_field_name("arguments")
        if otext == "Files" and ntext in _FILES_METHODS:
            return "Files." + ntext, node.child_by_field_name("arguments")
    return None


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        if _mitigated(method, src_b):
            continue
        tainted = _tainted_vars(method, src_b)
        for node in find(method, "object_creation_expression", "method_invocation"):
            sink = _is_sink(node, src_b)
            if sink is None:
                continue
            label, args = sink
            if args is None:
                continue
            if not (_has_source(args, src_b) or _refs_tainted(args, src_b, tainted)):
                continue
            line, col, _, _ = span(node)
            out.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"{label}(...) builds a filesystem path from tainted input with no canonicalization + base-directory containment check",
                    "note": f"argument derives from a request/stream source and `{label}` is reached without getCanonicalPath/toRealPath + startsWith guard in this method",
                    "help": "canonicalize (getCanonicalFile/toRealPath) then verify the result startsWith an allowlisted base directory before opening the file",
                    "judge": True,
                }
            )
    return out

# rule: A field or method annotated @GuardedBy(lock) must only be accessed on code paths that provably hold the named lock.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "guarded-by-lock-held"

# ponytail: handles @GuardedBy fields only; @GuardedBy methods left to caller.
# Lock-held ceiling: synchronized(lock) block, synchronized instance method
# (lock=="this"), or a prior X.lock() call in the same method. Upgrade to CFG
# dominator analysis if lock/unlock branching matters.


def _unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1]
    return s


def _guard_lock(field, sb):
    for ann in find(field, "annotation"):
        name = ann.child_by_field_name("name")
        if name is None or node_text(name, sb) != "GuardedBy":
            continue
        args = ann.child_by_field_name("arguments")
        if args is None:
            return None
        lits = find(args, "string_literal")
        if lits:
            return _unquote(node_text(lits[0], sb))
        return node_text(args, sb).strip("()").strip()
    return None


def _is_synchronized(m, sb):
    for c in m.children:
        if c.type == "modifiers":
            return "synchronized" in node_text(c, sb).split()
    return False


def _held(node, sb, lock, sync_method, lock_calls):
    cur = node.parent
    while cur is not None:
        if cur.type == "synchronized_statement":
            for ch in cur.children:
                if ch.type == "parenthesized_expression":
                    if node_text(ch, sb).strip()[1:-1].strip() == lock:
                        return True
        cur = cur.parent
    if sync_method and lock == "this":
        return True
    if lock in lock_calls and span(node)[0] >= lock_calls[lock]:
        return True
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    root = tree.root_node
    guarded = {}
    for fd in find(root, "field_declaration"):
        lock = _guard_lock(fd, sb)
        if lock is None:
            continue
        for vd in find(fd, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                guarded[node_text(nm, sb)] = lock
    if not guarded:
        return []
    findings = []
    for m in find(root, "method_declaration", "constructor_declaration"):
        body = m.child_by_field_name("body")
        if body is None:
            continue
        sync_method = _is_synchronized(m, sb)
        lock_calls = {}
        for inv in find(body, "method_invocation"):
            obj = inv.child_by_field_name("object")
            nm = inv.child_by_field_name("name")
            if obj is not None and nm is not None and node_text(nm, sb) == "lock":
                lock_calls.setdefault(node_text(obj, sb), span(inv)[0])
        for ident in find(body, "identifier"):
            name = node_text(ident, sb)
            if name not in guarded:
                continue
            p = ident.parent
            if p is not None and p.type == "variable_declarator":
                continue
            lock = guarded[name]
            if _held(ident, sb, lock, sync_method, lock_calls):
                continue
            ln, col = span(ident)[0], span(ident)[1]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": ln,
                    "col": col,
                    "message": "Access to @GuardedBy(\"%s\") field '%s' without holding lock %s."
                    % (lock, name, lock),
                    "note": "%s read/written outside a region that provably holds %s."
                    % (name, lock),
                    "help": "Wrap the access in synchronized(%s){...} or acquire %s before accessing '%s'."
                    % (lock, lock, name),
                }
            )
    return findings

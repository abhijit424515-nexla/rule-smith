# rule: A field accessed under a lock on some paths but read or written without that lock on others is inconsistently synchronized and races.
# (authored by RuleSmith from the description above)

# rule: A field accessed under a lock on some paths but read or written without that lock on others is inconsistently synchronized and races.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "inconsistent-field-synchronization"

# ponytail: "locked" ceiling = access sits inside synchronized(...) block, OR
# enclosing method is `synchronized`, OR a prior X.lock() call exists in the
# same method. Lock identity is ignored: any lock counts. Constructors are not
# racy (object not yet shared) so their accesses are skipped. final fields are
# skipped (their reference can't be reassigned). Upgrade to CFG + lock-identity
# matching if mixed-lock or branchy lock/unlock cases matter.


def _is_synchronized_method(m, sb):
    for c in m.children:
        if c.type == "modifiers":
            return "synchronized" in node_text(c, sb).split()
    return False


def _under_lock(node, sync_method, lock_line):
    cur = node.parent
    while cur is not None:
        if cur.type == "synchronized_statement":
            return True
        cur = cur.parent
    if sync_method:
        return True
    if lock_line is not None and span(node)[0] >= lock_line:
        return True
    return False


def _mutable_fields(root, sb):
    fields = set()
    for fd in find(root, "field_declaration"):
        is_final = False
        for c in fd.children:
            if c.type == "modifiers" and "final" in node_text(c, sb).split():
                is_final = True
        if is_final:
            continue
        for vd in find(fd, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                fields.add(node_text(nm, sb))
    return fields


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    root = tree.root_node
    fields = _mutable_fields(root, sb)
    if not fields:
        return []

    # field -> {"locked": bool, "unlocked": [access_node, ...]}
    seen = {f: {"locked": False, "unlocked": []} for f in fields}

    for m in find(root, "method_declaration"):
        body = m.child_by_field_name("body")
        if body is None:
            continue
        sync_method = _is_synchronized_method(m, sb)

        # earliest X.lock() call in this method (any lock object)
        lock_line = None
        for inv in find(body, "method_invocation"):
            nm = inv.child_by_field_name("name")
            if nm is not None and node_text(nm, sb) == "lock":
                ln = span(inv)[0]
                lock_line = ln if lock_line is None else min(lock_line, ln)

        # locals that shadow a field name -> not a field access in this method
        locals_ = set()
        for lv in find(body, "local_variable_declaration"):
            for vd in find(lv, "variable_declarator"):
                nm = vd.child_by_field_name("name")
                if nm is not None:
                    locals_.add(node_text(nm, sb))

        for ident in find(body, "identifier"):
            name = node_text(ident, sb)
            if name not in fields or name in locals_:
                continue
            p = ident.parent
            if p is not None and p.type in ("variable_declarator", "method_invocation"):
                continue
            if _under_lock(ident, sync_method, lock_line):
                seen[name]["locked"] = True
            else:
                seen[name]["unlocked"].append(ident)

    findings = []
    for name, st in seen.items():
        if not st["locked"] or not st["unlocked"]:
            continue
        for ident in st["unlocked"]:
            ln, col = span(ident)[0], span(ident)[1]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": ln,
                    "col": col,
                    "message": "Field '%s' is accessed under a lock elsewhere but here without one."
                    % name,
                    "note": "'%s' is read/written under synchronization on some paths and unguarded on this one."
                    % name,
                    "help": "Guard every access to '%s' with the same lock, or make it final/volatile if a lock is not needed."
                    % name,
                }
            )
    return findings

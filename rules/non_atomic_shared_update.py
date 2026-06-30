# rule: A read-modify-write or check-then-act (x++, x+=, x=x+1) on a shared or volatile field outside a lock is not atomic and loses updates.
# (authored by RuleSmith from the description above)

# rule: A read-modify-write or check-then-act (x++, x+=, x=x+1) on a shared or volatile field outside a lock is not atomic and loses updates.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "non-atomic-shared-update"

# ponytail: "shared" ceiling = field is volatile OR carries a @GuardedBy
# annotation. Those are the fields whose RMW races people actually hit
# (volatile gives visibility but NOT atomicity for ++/+=). "outside a lock" =
# not lexically inside synchronized(...), not in a synchronized method, and no
# prior X.lock() call in the method. Constructors are skipped (object not yet
# shared). Locals shadowing a field name are skipped. Upgrade to lock-identity
# + CFG matching if mixed-lock or branchy lock/unlock cases matter.

_COMPOUND = {"+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>=", ">>>="}


def _shared_fields(root, sb):
    fields = set()
    for fd in find(root, "field_declaration"):
        is_shared = False
        for c in fd.children:
            if c.type == "modifiers":
                txt = node_text(c, sb)
                if "volatile" in txt.split() or "GuardedBy" in txt:
                    is_shared = True
        if not is_shared:
            continue
        for vd in find(fd, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                fields.add(node_text(nm, sb))
    return fields


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


def _target_field(operand, sb, fields):
    # identifier 'x' or field_access 'this.x' -> field name if it is a shared field
    if operand is None:
        return None
    if operand.type == "identifier":
        nm = node_text(operand, sb)
        return nm if nm in fields else None
    if operand.type == "field_access":
        obj = operand.child_by_field_name("object")
        fld = operand.child_by_field_name("field")
        if obj is not None and fld is not None and node_text(obj, sb) == "this":
            nm = node_text(fld, sb)
            return nm if nm in fields else None
    return None


def _mutations(body, sb, fields):
    # yield (field_name, node) for each read-modify-write / check-then-act
    out = []
    for ue in find(body, "update_expression"):  # x++ / ++x / x-- / --x
        operand = None
        for c in ue.children:
            if c.type in ("identifier", "field_access"):
                operand = c
                break
        name = _target_field(operand, sb, fields)
        if name is not None:
            out.append((name, ue))
    for ae in find(body, "assignment_expression"):
        left = ae.child_by_field_name("left")
        op = ae.child_by_field_name("operator")
        name = _target_field(left, sb, fields)
        if name is None or op is None:
            continue
        op_txt = node_text(op, sb)
        if op_txt in _COMPOUND:
            out.append((name, ae))
        elif op_txt == "=":
            # x = x + 1  -> field read on the right-hand side
            right = ae.child_by_field_name("right")
            if right is not None and any(
                node_text(i, sb) == name for i in find(right, "identifier")
            ):
                out.append((name, ae))
    return out


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    root = tree.root_node
    fields = _shared_fields(root, sb)
    if not fields:
        return []

    findings = []
    for m in find(root, "method_declaration"):
        body = m.child_by_field_name("body")
        if body is None:
            continue
        sync_method = _is_synchronized_method(m, sb)

        lock_line = None
        for inv in find(body, "method_invocation"):
            nm = inv.child_by_field_name("name")
            if nm is not None and node_text(nm, sb) == "lock":
                ln = span(inv)[0]
                lock_line = ln if lock_line is None else min(lock_line, ln)

        locals_ = set()
        for lv in find(body, "local_variable_declaration"):
            for vd in find(lv, "variable_declarator"):
                nm = vd.child_by_field_name("name")
                if nm is not None:
                    locals_.add(node_text(nm, sb))

        for name, node in _mutations(body, sb, fields):
            if name in locals_:
                continue
            if _under_lock(node, sync_method, lock_line):
                continue
            ln, col = span(node)[0], span(node)[1]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": ln,
                    "col": col,
                    "message": "Non-atomic update of shared field '%s' outside a lock."
                    % name,
                    "note": "'%s' is volatile/@GuardedBy; read-modify-write here is not atomic and can lose concurrent updates."
                    % name,
                    "help": "Guard the update with the field's lock, or use an AtomicInteger/AtomicLong/LongAdder.",
                }
            )
    return findings

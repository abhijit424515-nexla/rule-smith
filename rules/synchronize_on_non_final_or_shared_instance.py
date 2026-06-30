# rule: Synchronizing on a non-final/reassigned field, or on a boxed primitive, interned String, or other cached/shared instance, gives no real mutual exclusion or enables unrelated-code deadlock.
# (authored by RuleSmith from the description above)

# rule: Synchronizing on a non-final/reassigned field, or on a boxed primitive, interned String, or other cached/shared instance, gives no real mutual exclusion or enables unrelated-code deadlock.
"""Flag synchronized blocks whose lock is a non-final field, a boxed primitive, or an interned/shared String."""

from rulesmith.parse import parse, find, span, node_text

RULE = "synchronize-on-non-final-or-shared-instance"

BOXED = {"Integer", "Long", "Short", "Byte", "Character", "Boolean", "Float", "Double"}


def _fields(root, src_b):
    info = {}
    for fd in find(root, "field_declaration"):
        mods = ""
        for ch in fd.children:
            if ch.type == "modifiers":
                mods = node_text(ch, src_b)
        t = fd.child_by_field_name("type")
        type_text = node_text(t, src_b) if t is not None else None
        is_final = "final" in mods.split()
        for vd in find(fd, "variable_declarator"):
            n = vd.child_by_field_name("name")
            if n is not None:
                info[node_text(n, src_b)] = (is_final, type_text)
    return info


def _classify(fname, is_final, ftype):
    base = ftype.split("<")[0].strip() if ftype else None
    if not is_final:
        return (
            f"synchronizing on non-final field '{fname}' (lock identity can change)",
            f"field '{fname}' is not declared final",
            "declare the lock field final, or use a dedicated private final Object",
        )
    if base in BOXED:
        return (
            f"synchronizing on boxed primitive field '{fname}' ({base} is cached/shared)",
            f"field '{fname}' has type {ftype}",
            "lock on a private final Object instead",
        )
    if base == "String":
        return (
            f"synchronizing on String field '{fname}' (may be interned/shared)",
            f"field '{fname}' has type {ftype}",
            "lock on a private final Object instead",
        )
    return (None, None, None)


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node
    fields = _fields(root, src_b)
    findings = []
    for sync in find(root, "synchronized_statement"):
        paren = None
        for ch in sync.children:
            if ch.type == "parenthesized_expression":
                paren = ch
                break
        if paren is None:
            continue
        lock = None
        for ch in paren.named_children:
            lock = ch
            break
        if lock is None:
            continue
        line, col = span(lock)[0], span(lock)[1]
        text = node_text(lock, src_b)
        msg = note = help_ = None

        if lock.type == "string_literal":
            msg = "synchronizing on a String literal (interned, JVM-wide shared)"
            note = f"lock = {text}"
            help_ = "lock on a private final Object instead"
        elif lock.type == "method_invocation":
            name = lock.child_by_field_name("name")
            if name is not None and node_text(name, src_b) == "intern":
                msg = "synchronizing on an interned String (JVM-wide shared)"
                note = f"lock = {text}"
                help_ = "lock on a private final Object instead"
        elif lock.type == "field_access":
            obj = lock.child_by_field_name("object")
            fld = lock.child_by_field_name("field")
            if obj is not None and obj.type == "this" and fld is not None:
                fname = node_text(fld, src_b)
                if fname in fields:
                    msg, note, help_ = _classify(fname, *fields[fname])
            elif obj is not None and node_text(obj, src_b) in BOXED:
                msg = "synchronizing on a cached/shared instance"
                note = f"lock = {text}"
                help_ = "lock on a private final Object instead"
        elif lock.type == "identifier":
            if text in fields:
                msg, note, help_ = _classify(text, *fields[text])

        if msg:
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": msg,
                    "note": note,
                    "help": help_,
                }
            )
    return findings

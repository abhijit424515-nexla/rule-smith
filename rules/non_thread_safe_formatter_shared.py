# rule: Sharing a documented non-thread-safe object (SimpleDateFormat, DecimalFormat, Calendar, Matcher) across threads via a static or instance field without per-thread or synchronized access is a data race.
# (authored by RuleSmith from the description above)

# rule: Sharing a documented non-thread-safe object (SimpleDateFormat, DecimalFormat, Calendar, Matcher) across threads via a static or instance field without per-thread or synchronized access is a data race.

from rulesmith.parse import parse, find, span, node_text

RULE = "non-thread-safe-formatter-shared"

UNSAFE = {
    "SimpleDateFormat",
    "DecimalFormat",
    "Calendar",
    "GregorianCalendar",
    "Matcher",
}

# ponytail: name-based, no type resolution. "synchronized access" = every
# non-constructor use sits in a synchronized(...) block or a synchronized
# method; "per-thread" = field type is ThreadLocal<...>. Constructor/initializer
# uses skipped (object not yet shared). judge=True so --judge can drop FPs.


def _base_name(type_text):
    return type_text.split("<")[0].strip().split(".")[-1]


def _unsafe_fields(root, sb):
    # name -> declaration node (skip ThreadLocal<...> = per-thread)
    fields = {}
    for fd in find(root, "field_declaration"):
        ty = fd.child_by_field_name("type")
        if ty is None:
            continue
        text = node_text(ty, sb)
        if _base_name(text) == "ThreadLocal":
            continue
        if _base_name(text) not in UNSAFE:
            continue
        for vd in find(fd, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                fields[node_text(nm, sb)] = fd
    return fields


def _enclosing_method(node):
    cur = node.parent
    while cur is not None:
        if cur.type in ("method_declaration", "constructor_declaration"):
            return cur
        cur = cur.parent
    return None


def _is_synchronized_method(m, sb):
    for c in m.children:
        if c.type == "modifiers" and "synchronized" in node_text(c, sb).split():
            return True
    return False


def _under_sync_block(node):
    cur = node.parent
    while cur is not None and cur.type not in (
        "method_declaration",
        "constructor_declaration",
    ):
        if cur.type == "synchronized_statement":
            return True
        cur = cur.parent
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    root = tree.root_node
    fields = _unsafe_fields(root, sb)
    if not fields:
        return []

    # locals shadowing a field name are not field accesses
    locals_ = set()
    for lv in find(root, "local_variable_declaration"):
        for vd in find(lv, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                locals_.add(node_text(nm, sb))

    unguarded = {f: None for f in fields}  # field -> first unsynchronized access node
    for ident in find(root, "identifier"):
        name = node_text(ident, sb)
        if name not in fields or name in locals_:
            continue
        m = _enclosing_method(ident)
        if m is None or m.type == "constructor_declaration":
            continue  # not yet shared / not an in-method use (incl. the declarator)
        if _is_synchronized_method(m, sb) or _under_sync_block(ident):
            continue
        if unguarded[name] is None:
            unguarded[name] = ident

    findings = []
    for name, fd in fields.items():
        access = unguarded.get(name)
        if access is None:
            continue
        decl = fd.child_by_field_name("type")
        ty_text = _base_name(node_text(decl, sb)) if decl is not None else "object"
        ln, col = span(fd)[0], span(fd)[1]
        aln = span(access)[0]
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": ln,
                "col": col,
                "message": "Field '%s' is a non-thread-safe %s shared without per-thread or synchronized access."
                % (name, ty_text),
                "note": "'%s' is accessed at line %d outside any synchronized block/method and is not a ThreadLocal."
                % (name, aln),
                "help": "Wrap it in a ThreadLocal<%s>, guard every access with a lock, or construct a fresh instance per use."
                % ty_text,
                "judge": True,
            }
        )
    return findings

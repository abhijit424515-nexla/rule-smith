# rule: Reading an Atomic via get() then writing back with set() based on the read defeats atomicity; use compareAndSet/updateAndGet/incrementAndGet.
# (authored by RuleSmith from the description above)

# rule: Reading an Atomic via get() then writing back with set() based on the read defeats atomicity; use compareAndSet/updateAndGet/incrementAndGet.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text, walk

RULE = "atomic-get-set-race"

# ponytail: "Atomic" = declared type name starts with "Atomic"
# (AtomicInteger/Long/Boolean/Reference/...). Two read-modify-write shapes:
#   A) x.set( ... x.get() ... )           inline get inside the set arg
#   B) v = x.get(); ...; x.set(... v ...) local read, then write derived from it
# Both lose updates under concurrency. compareAndSet/updateAndGet/getAndAdd are
# the atomic replacements. Per-method analysis; locals shadowing handled by
# only trusting v->x bindings seen in the same method before the set.


def _atomic_vars(root, sb):
    names = set()
    for decl in find(root, "field_declaration", "local_variable_declaration"):
        t = decl.child_by_field_name("type")
        if t is None or not node_text(t, sb).split("<")[0].strip().startswith("Atomic"):
            continue
        for vd in find(decl, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is not None:
                names.add(node_text(nm, sb))
    return names


def _call(node):
    return node is not None and node.type == "method_invocation"


def _obj_name(inv, sb):
    o = inv.child_by_field_name("object")
    return node_text(o, sb) if o is not None and o.type == "identifier" else None


def _name(inv, sb):
    n = inv.child_by_field_name("name")
    return node_text(n, sb) if n is not None else None


def _get_target(inv, sb, atomics):
    # method_invocation x.get() on an atomic var -> returns x
    if _call(inv) and _name(inv, sb) == "get":
        o = _obj_name(inv, sb)
        if o in atomics:
            args = inv.child_by_field_name("arguments")
            if args is None or all(c.type in ("(", ")") for c in args.children):
                return o
    return None


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    root = tree.root_node
    atomics = _atomic_vars(root, sb)
    if not atomics:
        return []

    findings = []
    for m in find(root, "method_declaration", "constructor_declaration"):
        body = m.child_by_field_name("body")
        if body is None:
            continue

        # build local-binding map: v -> (atomicVar, line) for v = x.get()
        bindings = {}
        for vd in find(body, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            val = vd.child_by_field_name("value")
            tgt = _get_target(val, sb, atomics) if val is not None else None
            if nm is not None and tgt is not None:
                bindings[node_text(nm, sb)] = (tgt, span(vd)[0])
        for ae in find(body, "assignment_expression"):
            left = ae.child_by_field_name("left")
            right = ae.child_by_field_name("right")
            tgt = _get_target(right, sb, atomics) if right is not None else None
            if left is not None and left.type == "identifier" and tgt is not None:
                bindings[node_text(left, sb)] = (tgt, span(ae)[0])

        for inv in find(body, "method_invocation"):
            if _name(inv, sb) != "set":
                continue
            x = _obj_name(inv, sb)
            if x not in atomics:
                continue
            args = inv.child_by_field_name("arguments")
            if args is None:
                continue
            set_line = span(inv)[0]

            # A) inline x.get() inside the set argument
            inline = any(_get_target(c, sb, atomics) == x for c in walk(args))
            # B) a local bound from x.get() earlier is read in the arg
            via_local = None
            for ident in find(args, "identifier"):
                nm = node_text(ident, sb)
                b = bindings.get(nm)
                if b is not None and b[0] == x and b[1] < set_line:
                    via_local = nm
                    break

            if inline:
                ev = "value passed to %s.set(...) is computed from %s.get()" % (x, x)
            elif via_local is not None:
                ev = "%s.set(...) writes back '%s', read earlier from %s.get()" % (
                    x,
                    via_local,
                    x,
                )
            else:
                continue

            ln, col = span(inv)[0], span(inv)[1]
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": ln,
                    "col": col,
                    "message": "Non-atomic get-then-set on Atomic '%s' loses concurrent updates."
                    % x,
                    "note": ev
                    + "; another thread can update between the get and the set.",
                    "help": "Replace with %s.compareAndSet(...), %s.updateAndGet(...), or incrementAndGet()/getAndAdd()."
                    % (x, x),
                }
            )
    return findings

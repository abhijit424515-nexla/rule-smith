# rule: A non-final mutable static field or static collection/array written or mutated without synchronization is unguarded cross-thread shared state.
# (authored by RuleSmith from the description above)

# rule: A non-final mutable static field or static collection/array written or mutated without synchronization is unguarded cross-thread shared state.
"""Flag non-final mutable static fields/collections/arrays written or mutated without synchronization."""

from rulesmith.parse import parse, find, span, node_text

RULE = "mutable-static-field-without-sync"

# names whose invocation mutates the receiver's state
MUTATORS = {
    "add",
    "addAll",
    "put",
    "putAll",
    "remove",
    "removeAll",
    "retainAll",
    "clear",
    "set",
    "push",
    "pop",
    "poll",
    "offer",
    "removeIf",
    "sort",
    "replace",
    "merge",
    "compute",
    "computeIfAbsent",
    "putIfAbsent",
}
# types that carry their own thread-safety
THREADSAFE_PREFIXES = ("Atomic",)
THREADSAFE_NAMES = (
    "ConcurrentHashMap",
    "ConcurrentMap",
    "ConcurrentLinkedQueue",
    "ConcurrentLinkedDeque",
    "CopyOnWriteArrayList",
    "CopyOnWriteArraySet",
    "ConcurrentSkipListMap",
    "ConcurrentSkipListSet",
    "BlockingQueue",
    "BlockingDeque",
    "LinkedBlockingQueue",
    "ArrayBlockingQueue",
)


def _mods(node, src_b):
    for ch in node.children:
        if ch.type == "modifiers":
            return node_text(ch, src_b)
    return ""


def _base_name(node, src_b):
    """Resolve identifier / field_access / array_access down to its base name."""
    if node is None:
        return None
    t = node.type
    if t == "identifier":
        return node_text(node, src_b)
    if t == "field_access":
        f = node.child_by_field_name("field")
        return node_text(f, src_b) if f is not None else None
    if t == "array_access":
        return _base_name(node.child_by_field_name("array"), src_b)
    return None


def _synchronized(node, src_b):
    """True if some ancestor guards this access (synchronized block/method, static init)."""
    p = node.parent
    while p is not None:
        if p.type == "synchronized_statement":
            return True
        if p.type == "static_initializer":
            return True  # runs once at class load, single-threaded
        if p.type in ("method_declaration", "constructor_declaration"):
            return "synchronized" in _mods(p, src_b).split()
        p = p.parent
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node

    # 1. collect non-final static fields
    fields = {}
    for fd in find(root, "field_declaration"):
        toks = _mods(fd, src_b).split()
        if "static" not in toks or "final" in toks:
            continue
        tnode = fd.child_by_field_name("type")
        ttext = node_text(tnode, src_b) if tnode is not None else ""
        threadsafe = ttext.startswith(THREADSAFE_PREFIXES) or any(
            n in ttext for n in THREADSAFE_NAMES
        )
        volatile = "volatile" in toks
        for vd in find(fd, "variable_declarator"):
            nm = vd.child_by_field_name("name")
            if nm is None:
                continue
            fields[node_text(nm, src_b)] = {
                "type": ttext,
                "volatile": volatile,
                "threadsafe": threadsafe,
            }

    if not fields:
        return []

    findings = []
    flagged = set()

    def emit(name, node, kind):
        if name in flagged:
            return
        flagged.add(name)
        f = fields[name]
        lno, c, _, _ = span(node)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": lno,
                "col": c,
                "message": f"non-final static field '{name}' {kind} without synchronization",
                "note": f"static {f['type']} '{name}' is shared across threads; {kind} is not guarded by a lock",
                "help": "guard with synchronized/Lock, make it final + immutable, or use an Atomic*/Concurrent* type",
                "judge": True,
            }
        )

    # 2. reassignments and array-element writes
    for asn in find(root, "assignment_expression"):
        left = asn.child_by_field_name("left")
        if left is None:
            continue
        array_write = left.type == "array_access"
        name = _base_name(left, src_b)
        if name not in fields:
            continue
        f = fields[name]
        if f["threadsafe"]:
            continue
        # volatile makes a plain reference reassignment atomic+visible; array elements it does not
        if not array_write and f["volatile"]:
            continue
        if _synchronized(asn, src_b):
            continue
        emit(name, asn, "array element written" if array_write else "reassigned")

    # 3. ++ / -- (never atomic, volatile does not help)
    for upd in find(root, "update_expression"):
        operand = None
        for ch in upd.children:
            if ch.type in ("identifier", "field_access", "array_access"):
                operand = ch
                break
        name = _base_name(operand, src_b)
        if name not in fields:
            continue
        if fields[name]["threadsafe"]:
            continue
        if _synchronized(upd, src_b):
            continue
        emit(name, upd, "incremented/decremented")

    # 4. mutating method calls on the field (collection/array contents)
    for mi in find(root, "method_invocation"):
        obj = mi.child_by_field_name("object")
        nm = mi.child_by_field_name("name")
        if obj is None or nm is None:
            continue
        if node_text(nm, src_b) not in MUTATORS:
            continue
        name = _base_name(obj, src_b)
        if name not in fields:
            continue
        if fields[name]["threadsafe"]:
            continue
        if _synchronized(mi, src_b):
            continue
        emit(name, mi, f"mutated via {node_text(nm, src_b)}()")

    return findings

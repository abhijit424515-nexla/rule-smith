"""Phase 1 primitives: intraprocedural CFG + dominance / post-dominance.

The workhorse for the detective rules (resource-leak, NPE, init-before-use,
typestate). dominates(a,b) = "a on every path to b"; postdom(a,b) = "b on
every path after a". Both are hard yes/no facts a verdict can cite as evidence.

Coverage: sequential stmts, if/else, while, for, enhanced-for, return, throw,
break, continue, try/catch/finally. Exception model is coarse (see ponytail
comments) -- exact enough for must-close / must-run-on-all-paths questions.
"""
from .parse import parse, span, node_text

SIMPLE_FALLTHROUGH = None  # default: any unrecognized statement falls through


class Node:
    __slots__ = ("id", "ts", "label", "succ", "pred")

    def __init__(self, nid, ts=None, label=None):
        self.id = nid
        self.ts = ts
        self.label = label or (ts.type if ts is not None else "synthetic")
        self.succ = set()
        self.pred = set()


class CFG:
    def __init__(self):
        self._c = 0
        self.nodes = {}
        self.entry = self.new(label="ENTRY")
        self.exit = self.new(label="EXIT")

    def new(self, ts=None, label=None):
        n = Node(self._c, ts, label)
        self.nodes[self._c] = n
        self._c += 1
        return n

    def edge(self, a, b):
        if a is None or b is None:
            return
        a.succ.add(b.id)
        b.pred.add(a.id)


class _Loop:
    def __init__(self, cont):
        self.cont = cont       # continue target
        self.breaks = []       # break nodes (route to loop exit)


class _Ctx:
    def __init__(self):
        self.loops = []        # stack of _Loop
        self.catches = []      # stack of catch-entry nodes (nearest last)
        self.finallies = []    # stack of finally-entry nodes (nearest last)


# statement types handled explicitly; everything else = simple fallthrough node
_CONTROL = {
    "if_statement", "while_statement", "for_statement",
    "enhanced_for_statement", "do_statement", "block",
    "return_statement", "throw_statement", "break_statement",
    "continue_statement", "try_statement", "try_with_resources_statement",
    "labeled_statement",
}


def build_method(method_ts, src_b=None):
    """Build a CFG for a method_declaration / constructor_declaration node."""
    body = method_ts.child_by_field_name("body")
    cfg = CFG()
    if body is None:
        cfg.edge(cfg.entry, cfg.exit)
        return cfg
    ctx = _Ctx()
    e, exits = _build(cfg, body, ctx)
    cfg.edge(cfg.entry, e)
    for x in exits:
        cfg.edge(x, cfg.exit)
    return cfg


def _stmts(block):
    return [c for c in block.children if c.is_named and c.type != "comment"]


def _build_seq(cfg, stmts, ctx):
    first = None
    prev = None
    for s in stmts:
        e, x = _build(cfg, s, ctx)
        if e is None:
            continue
        if first is None:
            first = e
        if prev is not None:
            for p in prev:
                cfg.edge(p, e)
        prev = x
    if first is None:
        n = cfg.new(label="empty")
        return n, [n]
    return first, (prev or [])


def _build(cfg, s, ctx):
    t = s.type
    if t == "block":
        return _build_seq(cfg, _stmts(s), ctx)
    if t == "labeled_statement":
        # ponytail: treat labeled stmt as its inner stmt; labeled break/continue
        # not yet resolved to the named loop (rare). Upgrade if it shows up.
        inner = [c for c in s.children if c.is_named and c.type != "identifier"]
        return _build_seq(cfg, inner, ctx)
    if t == "if_statement":
        return _build_if(cfg, s, ctx)
    if t in ("while_statement", "for_statement", "enhanced_for_statement", "do_statement"):
        return _build_loop(cfg, s, ctx)
    if t in ("return_statement", "throw_statement"):
        n = cfg.new(s, t)
        if t == "throw_statement" and ctx.catches:
            cfg.edge(n, ctx.catches[-1])
        elif ctx.finallies:
            cfg.edge(n, ctx.finallies[-1])
        else:
            cfg.edge(n, cfg.exit)
        return n, []           # no normal fallthrough
    if t == "break_statement":
        n = cfg.new(s, "break")
        if ctx.loops:
            ctx.loops[-1].breaks.append(n)
        return n, []
    if t == "continue_statement":
        n = cfg.new(s, "continue")
        if ctx.loops:
            cfg.edge(n, ctx.loops[-1].cont)
        return n, []
    if t in ("try_statement", "try_with_resources_statement"):
        return _build_try(cfg, s, ctx)
    # default: a simple statement that falls through
    n = cfg.new(s, t)
    return n, [n]


def _build_if(cfg, s, ctx):
    cond = cfg.new(s, "if")
    cons = s.child_by_field_name("consequence")
    alt = s.child_by_field_name("alternative")
    exits = []
    if cons is not None:
        ce, cx = _build(cfg, cons, ctx)
        cfg.edge(cond, ce)
        exits += cx
    else:
        exits.append(cond)
    if alt is not None:
        ae, ax = _build(cfg, alt, ctx)
        cfg.edge(cond, ae)
        exits += ax
    else:
        exits.append(cond)     # false branch falls through
    return cond, exits


def _build_loop(cfg, s, ctx):
    head = cfg.new(s, s.type)
    loop = _Loop(cont=head)
    ctx.loops.append(loop)
    body = s.child_by_field_name("body")
    if body is not None:
        be, bx = _build(cfg, body, ctx)
        cfg.edge(head, be)
        for p in bx:
            cfg.edge(p, head)  # back edge
    ctx.loops.pop()
    # loop exits: condition false (head) + any break
    do = s.type == "do_statement"
    entry = be if (do and body is not None) else head
    return entry, [head] + loop.breaks


def _build_try(cfg, s, ctx):
    body = s.child_by_field_name("body")
    catches = [c for c in s.children if c.type == "catch_clause"]
    fin = next((c for c in s.children if c.type == "finally_clause"), None)

    # build finally first so body/catch throws can target it
    fin_entry, fin_exits = (None, None)
    if fin is not None:
        fblock = next((c for c in fin.children if c.type == "block"), None)
        if fblock is not None:
            fin_entry, fin_exits = _build(cfg, fblock, ctx)

    # build catches; their entries are exception targets for the try body
    catch_entries = []
    catch_exits = []
    for cc in catches:
        cblock = next((c for c in cc.children if c.type == "block"), None)
        if cblock is not None:
            ce, cx = _build(cfg, cblock, ctx)
            catch_entries.append(ce)
            catch_exits += cx

    # body: push exception target (nearest catch, else finally)
    if catch_entries:
        ctx.catches.append(catch_entries[0])
    if fin_entry is not None:
        ctx.finallies.append(fin_entry)
    be, bx = (None, [])
    if body is not None:
        be, bx = _build(cfg, body, ctx)
        # coarse exception edge: try body may throw at entry -> catch/finally.
        # ponytail: entry-level approx, not per-statement. Enough to make a
        # trailing close() NOT post-dominate the body (leak detection works);
        # upgrade to per-statement exception edges if false negatives appear.
        if catch_entries:
            cfg.edge(be, catch_entries[0])
        elif fin_entry is not None:
            cfg.edge(be, fin_entry)
    if fin_entry is not None:
        ctx.finallies.pop()
    if catch_entries:
        ctx.catches.pop()

    normal_exits = list(bx) + catch_exits
    if fin_entry is not None:
        for p in normal_exits:
            cfg.edge(p, fin_entry)
        return (be or fin_entry), (fin_exits or [])
    return (be or (catch_entries[0] if catch_entries else None)), normal_exits


# ---- dominance ----------------------------------------------------------

def _dominators(cfg, succ_of, pred_of, roots):
    ids = list(cfg.nodes)
    full = set(ids)
    dom = {i: ({i} if i in roots else set(full)) for i in ids}
    changed = True
    while changed:
        changed = False
        for i in ids:
            if i in roots:
                continue
            preds = pred_of(i)
            inter = set(full)
            seen = False
            for p in preds:
                inter &= dom[p]
                seen = True
            new = {i} | (inter if seen else set())
            if new != dom[i]:
                dom[i] = new
                changed = True
    return dom


def dominators(cfg):
    return _dominators(
        cfg,
        succ_of=lambda i: cfg.nodes[i].succ,
        pred_of=lambda i: cfg.nodes[i].pred,
        roots={cfg.entry.id},
    )


def postdominators(cfg):
    # reverse the graph; post-dominators = dominators from EXIT backward
    return _dominators(
        cfg,
        succ_of=lambda i: cfg.nodes[i].pred,
        pred_of=lambda i: cfg.nodes[i].succ,
        roots={cfg.exit.id},
    )


def dominates(dom, a_id, b_id):
    """True if node a dominates node b (a on every path from entry to b)."""
    return a_id in dom.get(b_id, set())


def postdominates(pdom, a_id, b_id):
    """True if node a post-dominates node b (a on every path from b to exit)."""
    return a_id in pdom.get(b_id, set())


# ---- self-check ---------------------------------------------------------

def _method(src):
    tree, sb = parse(src)
    from .parse import find
    return find(tree.root_node, "method_declaration")[0], sb


def _find_call(cfg, name):
    """First CFG node whose ts text contains `name`."""
    for n in cfg.nodes.values():
        if n.ts is not None:
            txt = n.ts.text.decode("utf8", "replace")
            if name in txt:
                return n
    return None


def _demo():
    # 1. leak: close() after a return-on-error -> close does NOT postdom open
    leaky = """
    class A {
      void f(boolean err) {
        java.io.InputStream in = open();
        if (err) { return; }
        in.close();
      }
    }"""
    m, sb = _method(leaky)
    cfg = build_method(m, sb)
    pdom = postdominators(cfg)
    opn = _find_call(cfg, "open()")
    cls = _find_call(cfg, "close()")
    assert opn and cls
    assert not postdominates(pdom, cls.id, opn.id), "leak: close must NOT postdom open"

    # 2. safe: close() in finally -> close postdom open
    safe = """
    class A {
      void f() {
        java.io.InputStream in = open();
        try { use(in); } finally { in.close(); }
      }
    }"""
    m, sb = _method(safe)
    cfg = build_method(m, sb)
    pdom = postdominators(cfg)
    opn = _find_call(cfg, "open()")
    cls = _find_call(cfg, "close()")
    assert opn and cls
    assert postdominates(pdom, cls.id, opn.id), "safe: close in finally must postdom open"

    # 3. dominance: a null-guard dominates a guarded deref
    guarded = """
    class A {
      void f(String s) {
        if (s != null) { s.length(); }
      }
    }"""
    m, sb = _method(guarded)
    cfg = build_method(m, sb)
    dom = dominators(cfg)
    guard = _find_call(cfg, "s != null")
    deref = _find_call(cfg, "s.length()")
    assert guard and deref
    assert dominates(dom, guard.id, deref.id), "guard must dominate deref"

    print("cfg self-check: 3/3 passed (leak, safe-finally, guard-dominance)")


if __name__ == "__main__":
    _demo()

# rule: A value assigned to a local variable that is never read before being overwritten or going out of scope is useless and should be removed.
# (authored by RuleSmith from the description above)

# rule: A value assigned to a local variable that is never read before being overwritten or going out of scope is useless and should be removed.

"""Rule: dead-store (detective).

A local variable assignment whose value is never read before the variable is
overwritten or leaves scope is a dead store. Two provably-safe shapes:
  - overwrite: next write is a sibling statement in the SAME block with no read
    between the two writes (linear control flow, no branch in between).
  - out-of-scope: the last write to the variable is never read afterwards and is
    not inside a loop (where a textually-earlier read could execute after it).

Identity is keyed on start_byte, not id(): the tree-sitter Python binding hands
back a fresh Node wrapper per access, so id() of the same node varies.
"""

from rulesmith.parse import parse, find, span, node_text

RULE = "dead-store"

_LOOPS = ("while_statement", "for_statement", "do_statement", "enhanced_for_statement")


def _pos(node):
    line, col, _, _ = span(node)
    return (line, col)


def _block_id(node):
    p = node.parent
    while p is not None and p.type != "block":
        node, p = p, p.parent
    return p.start_byte if p is not None else None


def _in_loop(node):
    p = node.parent
    while p is not None:
        if p.type in _LOOPS:
            return True
        p = p.parent
    return False


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    methods = find(tree.root_node, "method_declaration", "constructor_declaration")
    for m in methods:
        # locals declared in this method
        declarators = []
        local_names = set()
        for decl in find(m, "local_variable_declaration"):
            for d in find(decl, "variable_declarator"):
                nn = d.child_by_field_name("name")
                if nn is not None:
                    local_names.add(node_text(nn, src_b))
                    declarators.append((d, nn))
        if not local_names:
            continue

        decl_name_bytes = set()
        store_target_bytes = set()
        stores = {n: [] for n in local_names}  # list of (pos, node)

        for d, nn in declarators:
            decl_name_bytes.add(nn.start_byte)
            if d.child_by_field_name("value") is not None:
                stores[node_text(nn, src_b)].append((_pos(nn), d))

        for a in find(m, "assignment_expression"):
            left = a.child_by_field_name("left")
            opn = a.child_by_field_name("operator")
            op = node_text(opn, src_b) if opn is not None else "="
            if left is not None and left.type == "identifier":
                lname = node_text(left, src_b)
                if lname in local_names and op == "=":
                    store_target_bytes.add(left.start_byte)
                    stores[lname].append((_pos(left), a))

        reads = {n: [] for n in local_names}
        for idn in find(m, "identifier"):
            t = node_text(idn, src_b)
            if (
                t in local_names
                and idn.start_byte not in decl_name_bytes
                and idn.start_byte not in store_target_bytes
            ):
                reads[t].append(_pos(idn))

        for name in local_names:
            sl = sorted(stores[name], key=lambda s: s[0])
            rl = sorted(reads[name])
            for i, (p, node) in enumerate(sl):
                nxt = sl[i + 1] if i + 1 < len(sl) else None
                dead = False
                why = ""
                if nxt is not None:
                    npos, _ = nxt
                    if _block_id(node) is not None and _block_id(node) == _block_id(
                        nxt[1]
                    ):
                        if not any(p < r < npos for r in rl):
                            dead = True
                            why = (
                                "being overwritten",
                                f"'{name}' is overwritten at line {npos[0]} with no read in between",
                            )
                else:
                    if not any(r > p for r in rl) and not _in_loop(node):
                        dead = True
                        why = (
                            "it goes out of scope",
                            f"'{name}' is never read after this assignment",
                        )
                if dead:
                    findings.append(
                        {
                            "rule": RULE,
                            "file": file,
                            "line": p[0],
                            "col": p[1],
                            "message": f"value assigned to '{name}' is never read before {why[0]}",
                            "note": why[1],
                            "help": "remove this assignment (and the declaration if the variable is otherwise unused)",
                            "judge": True,
                        }
                    )
    return findings

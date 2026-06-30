# rule: Local variables must be declared at the innermost block enclosing all their uses, not hoisted to method top.
# (authored by RuleSmith from the description above)

# rule: Local variables must be declared at the innermost block enclosing all their uses, not hoisted to method top.
"""Flag method-top local declarations whose every use sits inside one nested block."""

from rulesmith.parse import parse, find, span, node_text

RULE = "variable-scope-too-wide"

# statements that open a nested block the declaration could move into
BLOCK_BEARING = {
    "if_statement",
    "for_statement",
    "enhanced_for_statement",
    "while_statement",
    "do_statement",
    "try_statement",
    "switch_statement",
    "switch_expression",
    "synchronized_statement",
    "block",
}


def _top_level_ancestor(node, body_id):
    # walk up until parent is the method body block; return that direct child
    cur = node
    while cur.parent is not None and cur.parent.id != body_id:
        cur = cur.parent
    if cur.parent is None:
        return None
    return cur


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        body = method.child_by_field_name("body")
        if body is None or body.type != "block":
            continue
        top_decls = [
            c for c in body.named_children if c.type == "local_variable_declaration"
        ]
        if not top_decls:
            continue
        all_ids = find(method, "identifier")
        for decl in top_decls:
            for declr in find(decl, "variable_declarator"):
                nn = declr.child_by_field_name("name")
                if nn is None:
                    continue
                name = node_text(nn, src_b)
                # collect distinct top-level statements that actually use the var
                ancestors = {}
                for idn in all_ids:
                    if node_text(idn, src_b) != name:
                        continue
                    anc = _top_level_ancestor(idn, body.id)
                    if anc is None or anc.id == decl.id:
                        continue  # skip the declaration's own subtree (name + init)
                    ancestors[anc.id] = anc
                if len(ancestors) != 1:
                    continue  # zero uses (dead) or spans >1 top-level stmt: not too-wide
                stmt = next(iter(ancestors.values()))
                if stmt.type not in BLOCK_BEARING:
                    continue  # nowhere narrower to move it
                line, col, _, _ = span(nn)
                out.append(
                    {
                        "rule": RULE,
                        "file": file,
                        "line": line,
                        "col": col,
                        "message": f"local '{name}' is hoisted to method top but used only inside one nested {stmt.type}",
                        "note": f"every use of '{name}' is confined to a single {stmt.type} at line {span(stmt)[0]}",
                        "help": f"declare '{name}' inside that {stmt.type} block instead of at method top",
                    }
                )
    return out

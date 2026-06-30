# rule: A local variable assigned and returned (or thrown) on the very next statement should be inlined into the return.
# (authored by RuleSmith from the description above)

# rule: A local variable assigned and returned (or thrown) on the very next statement should be inlined into the return.
"""Inline a local variable that is assigned and immediately returned or thrown."""

from rulesmith.parse import parse, find, span, node_text

RULE = "assign-then-immediately-return"


def _single_declarator_name(decl):
    # exactly one declarator, and it must have an initializer
    decls = [c for c in decl.named_children if c.type == "variable_declarator"]
    if len(decls) != 1:
        return None
    d = decls[0]
    name = d.child_by_field_name("name")
    value = d.child_by_field_name("value")
    if name is None or value is None:
        return None
    return name


def _bare_identifier(stmt):
    # return/throw of a single bare identifier (not an expression, not empty)
    if stmt.type not in ("return_statement", "throw_statement"):
        return None
    exprs = stmt.named_children
    if len(exprs) != 1 or exprs[0].type != "identifier":
        return None
    return exprs[0]


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for block in find(tree.root_node, "block"):
        stmts = block.named_children  # comments are extra nodes, excluded
        for i in range(len(stmts) - 1):
            cur, nxt = stmts[i], stmts[i + 1]
            if cur.type != "local_variable_declaration":
                continue
            name = _single_declarator_name(cur)
            if name is None:
                continue
            ret = _bare_identifier(nxt)
            if ret is None:
                continue
            if node_text(name, src_b) != node_text(ret, src_b):
                continue
            line, col, _, _ = span(name)
            kw = "throw" if nxt.type == "throw_statement" else "return"
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": f"local '{node_text(name, src_b)}' is assigned then immediately {kw}n",
                    "note": node_text(cur, src_b) + " " + node_text(nxt, src_b),
                    "help": f"inline the initializer directly into the {kw}",
                }
            )
    return findings

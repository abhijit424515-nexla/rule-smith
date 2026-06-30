# rule: do not use a return statement inside a finally block

from rulesmith.parse import parse, find, node_text, span

RULE = "no-return-in-finally"

# Returns inside these node types belong to a nested scope, not the finally block.
_SCOPE = {
    "lambda_expression",
    "method_declaration",
    "constructor_declaration",
    "class_body",
}


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for fin in find(tree.root_node, "finally_clause"):
        for ret in find(fin, "return_statement"):
            # skip returns that live in a nested scope inside the finally
            n = ret.parent
            nested = False
            while n is not None and n != fin:
                if n.type in _SCOPE:
                    nested = True
                    break
                n = n.parent
            if nested:
                continue
            line, col, _, _ = span(ret)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Do not return from a finally block.",
                    "note": node_text(ret, src_bytes),
                    "help": "A return in finally swallows exceptions and discards returns from the try/catch. Move it out of finally.",
                }
            )
    return findings

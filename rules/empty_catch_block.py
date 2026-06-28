from rulesmith.parse import parse, find, span

RULE = "empty-catch-block"

def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    
    catch_clauses = find(tree.root_node, "catch_clause")
    
    for catch_clause in catch_clauses:
        block = None
        for child in catch_clause.children:
            if child.type == "block":
                block = child
                break
        
        if not block:
            continue
        
        has_statements = False
        for child in block.children:
            if child.type not in ("{", "}"):
                has_statements = True
                break
        
        if not has_statements:
            line, col, _, _ = span(catch_clause)
            findings.append({
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "Empty catch block swallows exception",
                "note": f"Catch clause at line {line} has no statements",
                "help": "Add exception handling, logging, or re-throw"
            })
    
    return findings
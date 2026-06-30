# rule: a method body must not exceed 60 lines

from rulesmith.parse import parse, find, span, node_text

RULE = "max-method-body-lines"
MAX_LINES = 60


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        body = method.child_by_field_name("body")
        if body is None:
            continue
        line, col, endline, _ = span(body)
        # body lines = lines spanned by the block, braces included
        body_lines = endline - line + 1
        if body_lines > MAX_LINES:
            name_node = method.child_by_field_name("name")
            name = node_text(name_node, src_bytes) if name_node else "<anonymous>"
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Method '%s' body is %d lines (max %d)."
                    % (name, body_lines, MAX_LINES),
                    "note": "body spans lines %d-%d" % (line, endline),
                    "help": "Split the method into smaller helpers so each body stays within %d lines."
                    % MAX_LINES,
                }
            )
    return findings

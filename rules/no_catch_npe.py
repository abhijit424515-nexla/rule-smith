# rule: do not catch NullPointerException; fix the root cause instead

from rulesmith.parse import parse, find, span, node_text

RULE = "no-catch-npe"

_BANNED = "NullPointerException"


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for clause in find(tree.root_node, "catch_clause"):
        # catch_type holds the caught exception type(s); multi-catch lists several.
        for ctype in find(clause, "catch_type"):
            for tid in find(ctype, "type_identifier"):
                name = node_text(tid, src_bytes)
                if name == _BANNED:
                    line, col, _, _ = span(tid)
                    findings.append(
                        {
                            "rule": RULE,
                            "file": file,
                            "line": line,
                            "col": col,
                            "message": "Do not catch NullPointerException; fix the root cause instead.",
                            "note": node_text(clause, src_bytes).splitlines()[0],
                            "help": "Add null checks or guarantee non-null inputs rather than catching NPE.",
                        }
                    )
    return findings

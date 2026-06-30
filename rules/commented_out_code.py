# rule: Flag blocks of commented-out source code (comment lines that parse as valid statements or declarations); version control makes them dead weight that misleads readers.
# (authored by RuleSmith from the description above)

# rule: Flag blocks of commented-out source code (comment lines that parse as valid statements or declarations); version control makes them dead weight that misleads readers.
"""Flag commented-out code: comments that parse as valid Java statements or declarations."""

from rulesmith.parse import parse, find, span, node_text

RULE = "commented-out-code"


def _strip_line(t):
    t = t.strip()
    if t.startswith("//"):
        t = t[2:]
    return t.strip()


def _strip_block(t):
    t = t.strip()
    if t.startswith("/*"):
        t = t[2:]
    if t.endswith("*/"):
        t = t[:-2]
    lines = []
    for ln in t.splitlines():
        ln = ln.strip()
        if ln.startswith("*"):
            ln = ln[1:].strip()
        lines.append(ln)
    return "\n".join(lines).strip()


def _looks_like_code(candidate):
    c = candidate.strip()
    if not c or not any(ch.isalpha() for ch in c):
        return False
    # real statements/declarations terminate with one of these; prose does not.
    return c[-1] in ";}{"


def _parse_clean(candidate):
    # try as a method body, then as a class member; clean parse on either => code.
    for wrap in (
        "class T { void m() {\n%s\n} }" % candidate,
        "class T {\n%s\n}" % candidate,
    ):
        tree, _ = parse(wrap)
        if not tree.root_node.has_error:
            return True
    return False


def _group(comments, src_b):
    # group runs of consecutive single-line comments; block comments stand alone.
    groups = []
    cur = []
    prev_line = None
    for n in comments:
        txt = node_text(n, src_b).strip()
        line = span(n)[0]
        if txt.startswith("//"):
            if cur and line == prev_line + 1:
                cur.append(n)
            else:
                if cur:
                    groups.append(cur)
                cur = [n]
            prev_line = line
        else:
            if cur:
                groups.append(cur)
                cur = []
            prev_line = None
            groups.append([n])
    if cur:
        groups.append(cur)
    return groups


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    comments = find(tree.root_node, "line_comment", "block_comment", "comment")
    comments.sort(key=lambda n: span(n)[0])

    findings = []
    for g in _group(comments, src_b):
        first = g[0]
        ftext = node_text(first, src_b)
        if ftext.strip().startswith("//"):
            candidate = "\n".join(_strip_line(node_text(n, src_b)) for n in g)
        else:
            candidate = _strip_block(ftext)
        if not _looks_like_code(candidate):
            continue
        if not _parse_clean(candidate):
            continue
        line, col = span(first)[0], span(first)[1]
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "commented-out code should be deleted; version control preserves history",
                "note": candidate.splitlines()[0][:80],
                "help": "delete the commented-out code",
            }
        )
    return findings

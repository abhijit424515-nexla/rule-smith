# rule: Flag the same group of 3+ parameters or fields (by name+type) recurring across multiple signatures or classes, indicating a missing parameter object or value class.
# (authored by RuleSmith from the description above)

# rule: Flag the same group of 3+ parameters or fields (by name+type) recurring across multiple signatures or classes, indicating a missing parameter object or value class.
"""Detect data clumps: a recurring group of 3+ (type,name) members across signatures/classes."""

from rulesmith.parse import parse, find, span, node_text

RULE = "data-clump-recurring-param-group"


def _pairs_from_params(params, src_b):
    s = set()
    for p in find(params, "formal_parameter"):
        t = p.child_by_field_name("type")
        n = p.child_by_field_name("name")
        if t and n:
            s.add((node_text(t, src_b).strip(), node_text(n, src_b).strip()))
    return s


def _pairs_from_class(body, src_b):
    s = set()
    for fd in find(body, "field_declaration"):
        t = fd.child_by_field_name("type")
        if not t:
            continue
        tt = node_text(t, src_b).strip()
        for vd in find(fd, "variable_declarator"):
            n = vd.child_by_field_name("name")
            if n:
                s.add((tt, node_text(n, src_b).strip()))
    return s


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    root = tree.root_node
    sources = []  # (line, col, label, frozenset(pairs))
    for m in find(root, "method_declaration", "constructor_declaration"):
        ps = find(m, "formal_parameters")
        if not ps:
            continue
        pairs = _pairs_from_params(ps[0], src_b)
        if pairs:
            lno, c = span(m)[0], span(m)[1]
            sources.append((lno, c, "signature", frozenset(pairs)))
    for cls in find(root, "class_declaration"):
        body = cls.child_by_field_name("body")
        if body is None:
            continue
        pairs = _pairs_from_class(body, src_b)
        if pairs:
            lno, c = span(cls)[0], span(cls)[1]
            sources.append((lno, c, "class fields", frozenset(pairs)))
    sources.sort(key=lambda s: (s[0], s[1]))

    # candidate clumps = pairwise intersections of size >= 3
    clumps = {}
    n = len(sources)
    for i in range(n):
        for j in range(i + 1, n):
            inter = sources[i][3] & sources[j][3]
            if len(inter) >= 3:
                clumps[inter] = True

    findings = []
    seen = set()
    for clump in clumps:
        holders = [s for s in sources if clump <= s[3]]
        if len(holders) < 2:
            continue
        first = holders[0]
        members = ", ".join(f"{t} {nm}" for t, nm in sorted(clump))
        note = f"group {{{members}}} appears together in {len(holders)} places"
        key = (first[0], first[1], note)
        if key in seen:
            continue
        seen.add(key)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": first[0],
                "col": first[1],
                "message": f"Data clump: {len(clump)} members recur across {len(holders)} signatures/classes",
                "note": note,
                "help": "Extract these recurring members into a parameter object / value class",
                "judge": True,
            }
        )
    return findings

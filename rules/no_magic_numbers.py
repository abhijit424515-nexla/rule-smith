# rule: do not use magic number literals other than -1, 0, 1, or 2 in expressions

from rulesmith.parse import parse, find, span, node_text

RULE = "no-magic-numbers"

_NUM_TYPES = (
    "decimal_integer_literal",
    "hex_integer_literal",
    "octal_integer_literal",
    "binary_integer_literal",
    "decimal_floating_point_literal",
    "hex_floating_point_literal",
)
_ALLOWED = {-1, 0, 1, 2}


def _value(text):
    t = text.replace("_", "")
    while t and t[-1] in "lLfFdD" and not t.lower().startswith("0x"):
        t = t[:-1]
    if not t:
        return None
    low = t.lower()
    try:
        if low.startswith("0x"):
            return int(t, 16)
        if low.startswith("0b"):
            return int(t[2:], 2)
        if "." in t or "e" in low:
            return float(t)
        if t.startswith("0") and len(t) > 1:
            return int(t, 8)
        return int(t)
    except ValueError:
        return None


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for lit in find(tree.root_node, *_NUM_TYPES):
        val = _value(node_text(lit, src_bytes))
        if val is None:
            continue
        # A leading unary minus belongs to the literal's numeric value.
        p = lit.parent
        if p is not None and p.type == "unary_expression":
            op = p.child_by_field_name("operator")
            if op is not None and node_text(op, src_bytes) == "-":
                val = -val
        if val in _ALLOWED:
            continue
        line, col, _el, _ec = span(lit)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "magic number literal in expression",
                "note": node_text(lit, src_bytes),
                "help": "Replace with a named constant; only -1, 0, 1, 2 are allowed inline.",
            }
        )
    return findings

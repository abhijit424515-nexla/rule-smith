# rule: A string compiled or used as a regex must be syntactically valid, and group(n) must reference a capture-group index the pattern actually defines.
# (authored by RuleSmith from the description above)

# rule: A string compiled or used as a regex must be syntactically valid, and group(n) must reference a capture-group index the pattern actually defines.
# (authored by RuleSmith from the description above)

"""Rule: valid-regex-and-group-index (detective).

A string literal handed to a regex API -- Pattern.compile, Pattern.matches,
or the String regex methods matches/replaceAll/replaceFirst/split -- must be a
syntactically valid pattern. We compile each such literal with Python's ``re``
and report a finding when it raises ``re.error`` (unbalanced parens, unclosed
character class, dangling quantifier, ...).

Separately, ``Matcher.group(n)`` must reference a capture-group index the
pattern defines. Within a method we link ``p = Pattern.compile(lit)`` ->
``m = p.matcher(x)`` -> ``m.group(n)`` and flag any ``n`` greater than the
pattern's capture-group count (group(0) is the whole match, always valid).

Conservative: only single string-literal patterns are inspected (computed /
concatenated patterns are skipped), and group-index checking requires the
pattern, matcher and group call to chain through named local variables.
"""

import re

from rulesmith.parse import parse, find, span, node_text

RULE = "valid-regex-and-group-index"

# Instance String methods whose first argument is a regex.
STRING_REGEX = {"matches", "replaceAll", "replaceFirst", "split"}


def _unquote(lit):
    if len(lit) >= 2 and lit[0] == '"' and lit[-1] == '"':
        return lit[1:-1]
    return lit


def _java_unescape(s):
    """Decode a Java string-literal body to the characters re should see."""
    out, i, n = [], 0, len(s)
    simple = {
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "b": "\b",
        "f": "\f",
        '"': '"',
        "'": "'",
        "\\": "\\",
    }
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            nxt = s[i + 1]
            if nxt in simple:
                out.append(simple[nxt])
            else:  # keep backslash for regex escapes like \d, \s, \w
                out.append("\\")
                out.append(nxt)
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _args(call):
    a = call.child_by_field_name("arguments")
    return [c for c in a.named_children] if a is not None else []


def _obj_text(call, src_b):
    o = call.child_by_field_name("object")
    return node_text(o, src_b) if o is not None else ""


def _name_text(call, src_b):
    n = call.child_by_field_name("name")
    return node_text(n, src_b) if n is not None else ""


def _regex_literal(call, src_b):
    """Return the string_literal node used as a regex by this call, or None."""
    name = _name_text(call, src_b)
    obj = _obj_text(call, src_b)
    args = _args(call)
    if not args:
        return None
    first = args[0]
    if first.type != "string_literal":
        return None
    if name == "compile" and obj.endswith("Pattern"):
        return first
    if name == "matches" and obj.endswith("Pattern"):
        return first  # Pattern.matches(regex, input)
    if name in STRING_REGEX:
        return first  # s.matches(regex) / s.replaceAll(regex, ...) / ...
    return None


def _compile(node, src_b):
    """(compiled_or_None, error_message_or_None) for a string_literal node."""
    pat = _java_unescape(_unquote(node_text(node, src_b)))
    try:
        return re.compile(pat), None
    except re.error as e:
        return None, str(e)


def _int_arg(call, src_b):
    args = _args(call)
    if len(args) == 1 and args[0].type == "decimal_integer_literal":
        try:
            return int(node_text(args[0], src_b))
        except ValueError:
            return None
    return None


def _check_method(method, src_b, file):
    out = []
    pattern_groups = {}  # pattern var -> capture-group count
    matcher_pattern = {}  # matcher var -> pattern var

    # First pass: validate every regex literal + record group counts per var.
    for call in find(method, "method_invocation"):
        lit = _regex_literal(call, src_b)
        if lit is None:
            continue
        compiled, err = _compile(lit, src_b)
        if compiled is None:
            line, col, *_ = span(lit)
            out.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Invalid regular expression: " + err,
                    "note": node_text(lit, src_b),
                    "help": "Fix the pattern syntax (balance ()/[], complete "
                    "quantifiers) so it compiles.",
                }
            )

    # Map named-variable chains: p = Pattern.compile(lit); m = p.matcher(x).
    for decl in find(method, "local_variable_declaration"):
        for vd in find(decl, "variable_declarator"):
            name_n = vd.child_by_field_name("name")
            val = vd.child_by_field_name("value")
            if name_n is None or val is None or val.type != "method_invocation":
                continue
            var = node_text(name_n, src_b)
            mname = _name_text(val, src_b)
            mobj = _obj_text(val, src_b)
            if mname == "compile" and mobj.endswith("Pattern"):
                args = _args(val)
                if args and args[0].type == "string_literal":
                    compiled, err = _compile(args[0], src_b)
                    if compiled is not None:
                        pattern_groups[var] = compiled.groups
            elif mname == "matcher" and mobj in pattern_groups:
                matcher_pattern[var] = mobj

    # Second pass: m.group(n) where n exceeds the pattern's group count.
    for call in find(method, "method_invocation"):
        if _name_text(call, src_b) != "group":
            continue
        obj = _obj_text(call, src_b)
        pvar = matcher_pattern.get(obj)
        if pvar is None:
            continue
        n = _int_arg(call, src_b)
        if n is None or n <= 0:
            continue
        count = pattern_groups[pvar]
        if n > count:
            line, col, *_ = span(call)
            out.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "group(%d) but pattern defines only %d capture "
                    "group(s)" % (n, count),
                    "note": node_text(call, src_b),
                    "help": "Reference a group index in 1..%d, or add the missing "
                    "capture group to the pattern." % count,
                }
            )
    return out


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    out = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        out += _check_method(m, src_b, file)
    return out

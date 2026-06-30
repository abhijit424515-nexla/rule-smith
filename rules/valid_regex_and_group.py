# rule: A string compiled or used as a regex must be syntactically valid, and group(n) must reference a capture-group index the pattern actually defines.
# (authored by RuleSmith from the description above)

# rule: A string compiled or used as a regex must be syntactically valid, and group(n) must reference a capture-group index the pattern actually defines.
# (authored by RuleSmith from the description above)

"""Rule: valid-regex-and-group (detective).

A string literal handed to a regex sink (Pattern.compile, Pattern.matches,
String.matches/split/replaceAll/replaceFirst) must be a syntactically valid
pattern, and Matcher.group(n) must reference a capture-group index the pattern
defines (0 = whole match; 1..k = the k groups it declares).
"""

import re

from rulesmith.parse import parse, find, span, node_text

RULE = "valid-regex-and-group"

REGEX_SINKS = {"compile", "matches", "split", "replaceAll", "replaceFirst"}

_ESC = {
    r"\n": "\n",
    r"\t": "\t",
    r"\r": "\r",
    r"\f": "\f",
    r"\b": "\b",
    r"\"": '"',
    r"\'": "'",
    "\\\\": "\\",
    r"\0": "\0",
}


def _unescape(s):
    if s in _ESC:
        return _ESC[s]
    if s.startswith("\\u"):
        return chr(int(s[2:], 16))
    if len(s) == 2:  # other single-char escape: take the escaped char
        return s[1]
    return s


def _str_value(node, src_b):
    parts = []
    for ch in node.children:
        if ch.type == "string_fragment":
            parts.append(node_text(ch, src_b))
        elif ch.type == "escape_sequence":
            parts.append(_unescape(node_text(ch, src_b)))
    return "".join(parts)


# ponytail: validate/count with Python re. Ceiling: Java-only constructs
# (\p, possessive quantifiers, atomic (?>...)) aren't valid in re, so we skip
# them rather than false-flag. Upgrade path: a real Java regex parser.
def _java_only(p):
    return any(t in p for t in ("\\p", "\\P", "(?>", "*+", "++", "?+", "}+"))


def _re_info(p):
    """('ok', group_count) | ('err', message) | ('skip', None)."""
    if _java_only(p):
        return ("skip", None)
    try:
        return ("ok", re.compile(p).groups)
    except re.error as e:
        return ("err", str(e))


def _first_str_arg(mi, src_b):
    args = mi.child_by_field_name("arguments")
    if args is None or not args.named_children:
        return None
    first = args.named_children[0]
    return _str_value(first, src_b) if first.type == "string_literal" else None


def _int_arg(mi, src_b):
    args = mi.child_by_field_name("arguments")
    if args is None or not args.named_children:
        return None
    first = args.named_children[0]
    if first.type == "decimal_integer_literal":
        return int(node_text(first, src_b))
    return None


def _is_regex_call(name, obj, src_b):
    if name == "compile":  # only Pattern.compile is a regex sink
        return (
            obj is not None
            and obj.type == "identifier"
            and node_text(obj, src_b) == "Pattern"
        )
    return True


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        pattern_vars = {}  # var -> group count (from Pattern.compile literal)
        matcher_vars = {}  # var -> group count (from patternvar.matcher(...))
        for decl in find(method, "local_variable_declaration"):
            for d in find(decl, "variable_declarator"):
                nm = d.child_by_field_name("name")
                val = d.child_by_field_name("value")
                if nm is None or val is None or val.type != "method_invocation":
                    continue
                vname = node_text(nm, src_b)
                obj = val.child_by_field_name("object")
                name_n = val.child_by_field_name("name")
                if name_n is None:
                    continue
                mname = node_text(name_n, src_b)
                if mname == "compile" and _is_regex_call("compile", obj, src_b):
                    lit = _first_str_arg(val, src_b)
                    if lit is not None:
                        status, info = _re_info(lit)
                        if status == "ok":
                            pattern_vars[vname] = info
                elif (
                    mname == "matcher" and obj is not None and obj.type == "identifier"
                ):
                    pv = node_text(obj, src_b)
                    if pv in pattern_vars:
                        matcher_vars[vname] = pattern_vars[pv]

        for mi in find(method, "method_invocation"):
            name_n = mi.child_by_field_name("name")
            if name_n is None:
                continue
            name = node_text(name_n, src_b)
            obj = mi.child_by_field_name("object")

            if name in REGEX_SINKS and _is_regex_call(name, obj, src_b):
                lit = _first_str_arg(mi, src_b)
                if lit is not None:
                    status, info = _re_info(lit)
                    if status == "err":
                        line, col, _, _ = span(mi)
                        findings.append(
                            {
                                "rule": RULE,
                                "file": file,
                                "line": line,
                                "col": col,
                                "message": f"Regex literal is not syntactically valid: {info}.",
                                "note": node_text(mi, src_b).strip(),
                                "help": "Fix the pattern; an invalid regex throws PatternSyntaxException at runtime.",
                            }
                        )

            if name == "group" and obj is not None and obj.type == "identifier":
                mv = node_text(obj, src_b)
                if mv in matcher_vars:
                    n = _int_arg(mi, src_b)
                    if n is not None and n > matcher_vars[mv]:
                        line, col, _, _ = span(mi)
                        cnt = matcher_vars[mv]
                        findings.append(
                            {
                                "rule": RULE,
                                "file": file,
                                "line": line,
                                "col": col,
                                "message": f"group({n}) references a capture group the pattern does not define (it has {cnt}).",
                                "note": node_text(mi, src_b).strip(),
                                "help": f"Use an index in 0..{cnt}; group(n) for n>{cnt} throws IndexOutOfBoundsException.",
                            }
                        )
    return findings

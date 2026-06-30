# rule: A format string passed to String.format/printf/log must have conversion specifiers whose count and types match the supplied varargs arguments.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "format-string-arity"

# Method names that take a printf-style format string as an argument.
ARG_FORMAT = {"format", "printf"}
# Integer conversions: reject string / float / boolean literals.
INT_CONV = set("dox")
# Floating conversions: reject string / boolean literals.
FLOAT_CONV = set("efga")


def _unquote(lit):
    """Strip the surrounding double quotes from a string_literal's text."""
    if len(lit) >= 2 and lit[0] == '"' and lit[-1] == '"':
        return lit[1:-1]
    return lit


def _parse_format(fmt):
    """Return (conv_chars, has_positional). conv_chars excludes %% and %n."""
    specs = []
    has_pos = False
    i, n = 0, len(fmt)
    while i < n:
        if fmt[i] != "%":
            i += 1
            continue
        i += 1  # consume '%'
        if i >= n:
            break
        if fmt[i] == "%":  # literal percent, no argument
            i += 1
            continue
        j = i
        # optional argument index: digits '$'
        k = j
        while k < n and fmt[k].isdigit():
            k += 1
        if k < n and k > j and fmt[k] == "$":
            has_pos = True
            j = k + 1
        # flags ('<' reuses the previous argument -> positional-like)
        while j < n and fmt[j] in "-#+ 0,(<":
            if fmt[j] == "<":
                has_pos = True
            j += 1
        # width
        while j < n and fmt[j].isdigit():
            j += 1
        # precision
        if j < n and fmt[j] == ".":
            j += 1
            while j < n and fmt[j].isdigit():
                j += 1
        if j >= n:
            break
        conv = fmt[j]
        if conv in "nN":  # newline, consumes no argument
            i = j + 1
            continue
        if conv in "tT":  # date/time conversion has a trailing suffix letter
            specs.append(conv)
            i = j + 2
            continue
        specs.append(conv)
        i = j + 1
    return specs, has_pos


def _type_mismatch(conv, arg_node):
    """True if an obvious literal arg cannot satisfy this conversion."""
    cl = conv.lower()
    t = arg_node.type
    if cl in INT_CONV:
        return t in (
            "string_literal",
            "decimal_floating_point_literal",
            "true",
            "false",
        )
    if cl in FLOAT_CONV:
        return t in ("string_literal", "true", "false")
    return False


def _string_args(arg_list):
    return [c for c in arg_list.named_children] if arg_list is not None else []


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for mi in find(tree.root_node, "method_invocation"):
        nm = mi.child_by_field_name("name")
        if nm is None:
            continue
        name = node_text(nm, src_b)
        args = _string_args(mi.child_by_field_name("arguments"))

        if name == "formatted":  # "fmt".formatted(args...)
            obj = mi.child_by_field_name("object")
            if obj is None or obj.type != "string_literal":
                continue
            fmt_node, varargs = obj, args
        elif name in ARG_FORMAT:  # String.format / out.printf
            idx = next(
                (i for i, a in enumerate(args) if a.type == "string_literal"), None
            )
            if idx is None:
                continue
            fmt_node, varargs = args[idx], args[idx + 1 :]
        else:
            continue

        # A lone array vararg expands at runtime -- arity is unknowable here.
        if len(varargs) == 1 and varargs[0].type == "array_creation_expression":
            continue

        specs, has_pos = _parse_format(_unquote(node_text(fmt_node, src_b)))
        if has_pos:  # positional / reuse formats are out of scope
            continue

        problem = None
        if len(specs) != len(varargs):
            problem = (
                f"format string has {len(specs)} conversion specifier(s) but "
                f"{len(varargs)} argument(s) were supplied"
            )
        else:
            for conv, arg in zip(specs, varargs):
                if _type_mismatch(conv, arg):
                    problem = (
                        f"argument '{node_text(arg, src_b).strip()}' cannot satisfy "
                        f"conversion '%{conv}'"
                    )
                    break
        if problem is None:
            continue

        line, col, _, _ = span(mi)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Format call mismatch: {problem}.",
                "note": node_text(mi, src_b).strip(),
                "help": (
                    "Make the number and types of conversion specifiers in the "
                    "format string match the supplied arguments; remember %% and "
                    "%n consume no argument."
                ),
            }
        )
    return findings

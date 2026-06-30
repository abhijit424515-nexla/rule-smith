# rule: Reference-returning methods that can have no result should return Optional rather than null, and must never return a null Optional.
# (authored by RuleSmith from the description above)

# rule: Reference-returning methods that can have no result should return Optional rather than null, and must never return a null Optional.

from rulesmith.parse import parse, find, node_text, span

RULE = "prefer-optional-over-null-return"

# Collections have their own rule (collection-return-no-null); don't double-flag.
_COLLECTION = {
    "List",
    "Set",
    "Map",
    "Collection",
    "Queue",
    "Deque",
    "Iterable",
    "SortedSet",
    "SortedMap",
    "NavigableSet",
    "NavigableMap",
    "ArrayList",
    "LinkedList",
    "HashSet",
    "TreeSet",
    "HashMap",
    "TreeMap",
    "Stream",
    "IntStream",
    "LongStream",
    "DoubleStream",
}
# return inside one of these belongs to a nested fn, not the method we're scanning.
_SCOPE = {"lambda_expression", "method_declaration", "constructor_declaration"}


def _base_name(type_node, sb):
    # strip generics + package: java.util.Optional<String> -> Optional
    return node_text(type_node, sb).split("<", 1)[0].strip().split(".")[-1]


def _returns_null(expr):
    if expr is None:
        return False
    if expr.type == "null_literal":
        return True
    if expr.type == "ternary_expression":
        for f in ("consequence", "alternative"):
            b = expr.child_by_field_name(f)
            if b is not None and b.type == "null_literal":
                return True
    return False


def analyze_source(src, file="<src>"):
    tree, sb = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        rtype = m.child_by_field_name("type")
        body = m.child_by_field_name("body")
        if rtype is None or body is None:
            continue
        # only reference return types (skip primitives, void, arrays).
        if rtype.type not in (
            "type_identifier",
            "scoped_type_identifier",
            "generic_type",
        ):
            continue
        base = _base_name(rtype, sb)
        if base in _COLLECTION:
            continue
        is_optional = base == "Optional"

        for ret in find(body, "return_statement"):
            # skip returns owned by a nested lambda/method.
            n, nested = ret.parent, False
            while n is not None and n != body:
                if n.type in _SCOPE:
                    nested = True
                    break
                n = n.parent
            if nested:
                continue
            expr = ret.child_by_field_name("value")
            if expr is None:
                kids = ret.named_children
                expr = kids[0] if kids else None
            if not _returns_null(expr):
                continue
            line, col, _, _ = span(ret)
            if is_optional:
                msg = "Method returning Optional must never return a null Optional."
                help_ = "Return Optional.empty() instead of null."
            else:
                msg = "Reference-returning method returns null; model absence with Optional."
                help_ = (
                    "Change the return type to Optional<%s> and return "
                    "Optional.empty() instead of null." % base
                )
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": msg,
                    "note": node_text(ret, sb).strip(),
                    "help": help_,
                }
            )
    return findings

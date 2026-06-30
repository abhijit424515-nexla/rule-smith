# rule: a method whose return type is a List, Set, Map, Collection, or array must not return null; return an empty one

from rulesmith.parse import parse, find, node_text, span

RULE = "collection-return-no-null"

# Collection-ish return types that must return an empty value, never null.
_COLLECTION = {
    "List",
    "Set",
    "Map",
    "Collection",
    "Queue",
    "Deque",
    "SortedSet",
    "SortedMap",
    "NavigableSet",
    "NavigableMap",
    "Iterable",
}

# Returns inside these node types belong to a nested function, not this method.
_SCOPE = {"lambda_expression", "method_declaration", "constructor_declaration"}


def _is_collection_type(type_node, src_bytes):
    if type_node is None:
        return False
    if type_node.type == "array_type":
        return True
    # List<String> -> generic_type wrapping the name; strip generics + package.
    text = node_text(type_node, src_bytes)
    base = text.split("<", 1)[0].strip()
    base = base.split(".")[-1]
    return base in _COLLECTION


def _null_returns(expr):
    # expr is the value returned. Flag direct null and ternary branches that are null.
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
    tree, src_bytes = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration"):
        if not _is_collection_type(m.child_by_field_name("type"), src_bytes):
            continue
        body = m.child_by_field_name("body")
        if body is None:
            continue
        for ret in find(body, "return_statement"):
            # skip returns owned by a nested lambda/method inside this body
            n = ret.parent
            nested = False
            while n is not None and n != body:
                if n.type in _SCOPE:
                    nested = True
                    break
                n = n.parent
            if nested:
                continue
            expr = ret.child_by_field_name("value")
            if expr is None:
                kids = [c for c in ret.named_children]
                expr = kids[0] if kids else None
            if not _null_returns(expr):
                continue
            line, col, _, _ = span(ret)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Method with collection/array return type must not return null.",
                    "note": node_text(ret, src_bytes),
                    "help": "Return an empty collection or array (e.g. Collections.emptyList(), new int[0]) instead of null.",
                }
            )
    return findings

# rule: Calls to partial extractors (Try.get, Either left/right projection .get, Option.get) rethrow or throw when the value is absent and should be replaced with safe folds/pattern matches.
# (authored by RuleSmith from the description above)

# rule: Calls to partial extractors (Try.get, Either left/right projection .get, Option.get) rethrow or throw when the value is absent and should be replaced with safe folds/pattern matches.
# (authored by RuleSmith from the description above)

"""Rule: partial-extractor-get (detective).

Partial extractors on monadic containers -- Try.get(), Either projection
left()/right().get() (and getLeft()/getRight()), Option/Optional.get() --
throw/rethrow when the value is absent. Flag every such call; the no-argument
shape distinguishes them from total accessors like Map.get(k)/List.get(i),
which always take an argument. Fix is a safe fold / pattern match
(fold, getOrElse, orElse, map, match).
"""

from rulesmith.parse import parse, find, span, node_text

RULE = "partial-extractor-get"

# Receiver types whose .get()/getLeft()/getRight() are partial (throw if absent).
MONAD_TYPES = {"Optional", "Option", "Try", "Either"}
# Static factories that produce one of the monad types: `Try.of(...).get()`.
FACTORIES = {"of", "ofNullable", "some", "none", "success", "failure", "empty"}
# Either projections: `e.left().get()` / `e.right().get()`.
PROJECTIONS = {"left", "right"}


def _simple(type_text):
    return type_text.split("<")[0].strip().split(".")[-1]


def _monad_vars(method_ts, src_b):
    """Names of locals/params declared with a monadic type."""
    names = set()
    decls = find(method_ts, "local_variable_declaration", "formal_parameter")
    for d in decls:
        ty = d.child_by_field_name("type")
        if ty is None:
            continue
        if _simple(node_text(ty, src_b)) not in MONAD_TYPES:
            continue
        if d.type == "formal_parameter":
            nm = d.child_by_field_name("name")
            if nm is not None:
                names.add(node_text(nm, src_b))
        else:
            for decl in find(d, "variable_declarator"):
                nm = decl.child_by_field_name("name")
                if nm is not None:
                    names.add(node_text(nm, src_b))
    return names


def _is_monadic(node, monad_vars, src_b):
    """Does this expression evaluate to a monadic container?"""
    if node is None:
        return False
    if node.type == "identifier":
        return node_text(node, src_b) in monad_vars
    if node.type == "method_invocation":
        nm = node.child_by_field_name("name")
        obj = node.child_by_field_name("object")
        if nm is None:
            return False
        name = node_text(nm, src_b)
        if name in PROJECTIONS:  # e.left() / e.right()
            return _is_monadic(obj, monad_vars, src_b)
        if name in FACTORIES and obj is not None and obj.type == "identifier":
            return node_text(obj, src_b) in MONAD_TYPES  # Try.of(...)
    return False


def _no_args(mi):
    args = mi.child_by_field_name("arguments")
    return args is not None and args.named_child_count == 0


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration", "constructor_declaration"):
        monad_vars = _monad_vars(method, src_b)
        for mi in find(method, "method_invocation"):
            nm = mi.child_by_field_name("name")
            if nm is None or not _no_args(mi):
                continue
            name = node_text(nm, src_b)
            obj = mi.child_by_field_name("object")
            kind = None
            if name == "get" and _is_monadic(obj, monad_vars, src_b):
                kind = "get()"
            elif (
                name in ("getLeft", "getRight")
                and obj is not None
                and (obj.type == "identifier" and node_text(obj, src_b) in monad_vars)
            ):
                kind = name + "()"
            if kind is None:
                continue
            line, col, _, _ = span(mi)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": (
                        f"Partial extractor '{kind}' throws/rethrows when the value is "
                        f"absent; replace with a safe fold or pattern match."
                    ),
                    "note": node_text(mi, src_b).strip(),
                    "help": (
                        "Use fold / match / getOrElse / orElse / map instead of "
                        "unwrapping with get(); never assume the container is non-empty."
                    ),
                }
            )
    return findings

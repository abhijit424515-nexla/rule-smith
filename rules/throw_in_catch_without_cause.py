# rule: Throwing a new exception inside a catch without chaining the caught exception as its cause discards the original stack trace and failure context.
# (authored by RuleSmith from the description above)

# rule: Throwing a new exception inside a catch without chaining the caught exception as its cause discards the original stack trace and failure context.

from rulesmith.parse import parse, find, span, node_text

RULE = "throw-in-catch-without-cause"


def _enclosing_catch(node):
    p = node.parent
    while p is not None:
        if p.type == "catch_clause":
            return p
        p = p.parent
    return None


def _catch_var(catch, src):
    # catch_formal_parameter: type is a *_type node, the variable is a plain identifier.
    for p in find(catch, "catch_formal_parameter"):
        ids = find(p, "identifier")
        if ids:
            return node_text(ids[-1], src)
    return None


def _thrown_new(throw_node):
    for c in throw_node.children:
        if c.type == "object_creation_expression":
            return c
    return None


def _chains(newexpr, varname, src):
    # Chained if caught var passed directly as a constructor argument: new X(.., e).
    args = newexpr.child_by_field_name("arguments")
    if args is None:
        return False
    for a in args.children:
        if a.type == "identifier" and node_text(a, src) == varname:
            return True
    return False


def _calls_initcause(catch, varname, src):
    for mi in find(catch, "method_invocation"):
        name = mi.child_by_field_name("name")
        if name is None or node_text(name, src) != "initCause":
            continue
        args = mi.child_by_field_name("arguments")
        if args and any(
            a.type == "identifier" and node_text(a, src) == varname
            for a in args.children
        ):
            return True
    return False


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for throw in find(tree.root_node, "throw_statement"):
        catch = _enclosing_catch(throw)
        if catch is None:
            continue
        newexpr = _thrown_new(throw)
        if newexpr is None:  # `throw e;` re-throw, not a new exception
            continue
        varname = _catch_var(catch, src_bytes)
        if varname is None:
            continue
        if _chains(newexpr, varname, src_bytes) or _calls_initcause(
            catch, varname, src_bytes
        ):
            continue
        line, col, _, _ = span(throw)
        new_type = newexpr.child_by_field_name("type")
        tname = node_text(new_type, src_bytes) if new_type else "exception"
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"Thrown '{tname}' does not chain caught '{varname}' as its cause.",
                "note": f"catch ({varname}) -> throw new {tname}(...)",
                "help": f"Pass '{varname}' as the cause, e.g. new {tname}(msg, {varname}), or call initCause({varname}).",
            }
        )
    return findings

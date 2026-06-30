# rule: A method taking a boolean parameter that selects between behaviors is a control-coupling smell and should be split into two methods.
# (authored by RuleSmith from the description above)

# rule: A method taking a boolean parameter that selects between behaviors is a control-coupling smell and should be split into two methods.
# (authored by RuleSmith from the description above)

from rulesmith.parse import parse, find, span, node_text

RULE = "boolean-selector-param"


_BOOL_TYPES = {"boolean", "Boolean"}


def _bool_params(method, src):
    """Return [(name, param_node)] for boolean-typed formal parameters."""
    out = []
    for fp in find(method, "formal_parameter"):
        t = fp.child_by_field_name("type")
        n = fp.child_by_field_name("name")
        if t is None or n is None:
            continue
        if node_text(t, src).strip() in _BOOL_TYPES:
            out.append((node_text(n, src), fp))
    return out


def _names_in(node, src):
    return {node_text(i, src) for i in find(node, "identifier")}


def _selects_on(method, name, src):
    """True if an if-statement or ternary branches on `name`.

    Branch = condition references the param AND there is a real fork
    (else clause for if; conditional_expression always forks).
    """
    for ifs in find(method, "if_statement"):
        cond = ifs.child_by_field_name("condition")
        if cond is None:
            continue
        if (
            name in _names_in(cond, src)
            and ifs.child_by_field_name("alternative") is not None
        ):
            return ifs
    for cx in find(method, "ternary_expression", "conditional_expression"):
        cond = cx.child_by_field_name("condition")
        if cond is None:
            continue
        if name in _names_in(cond, src):
            return cx
    return None


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for method in find(tree.root_node, "method_declaration"):
        for name, pnode in _bool_params(method, src_bytes):
            branch = _selects_on(method, name, src_bytes)
            if branch is None:
                continue
            line, col, _, _ = span(pnode)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "Boolean parameter '%s' selects between behaviors (control coupling)."
                    % name,
                    "note": node_text(branch, src_bytes)[:200],
                    "help": "Split into two methods, one per behavior, instead of a boolean flag.",
                }
            )
    return findings

# rule: Reflective field/method access, dynamic proxies, and runtime bytecode/lambda generation in critical paths obscure the call graph and defeat static analysis.
# (authored by RuleSmith from the description above)

# rule: Reflective field/method access, dynamic proxies, and runtime bytecode/lambda generation in critical paths obscure the call graph and defeat static analysis.
# (authored by RuleSmith from the description above)
"""Flag reflection, dynamic-proxy, and runtime bytecode/MethodHandle generation calls that hide edges from the static call graph."""

from rulesmith.parse import parse, find, span, node_text

RULE = "reflection-defeats-static-analysis"

# Method names that, by JDK convention, perform reflection / proxy /
# bytecode-or-handle generation. Name-based: false positives are possible on
# unrelated user methods of the same name, hence judge=True.
REFLECT = {
    # class/member discovery + access
    "forName",
    "getMethod",
    "getMethods",
    "getDeclaredMethod",
    "getDeclaredMethods",
    "getField",
    "getFields",
    "getDeclaredField",
    "getDeclaredFields",
    "getConstructor",
    "getConstructors",
    "getDeclaredConstructor",
    "getDeclaredConstructors",
    "setAccessible",
    "getDeclaringClass",
    # dynamic proxies
    "newProxyInstance",
    # runtime bytecode / MethodHandle / lambda metafactory generation
    "defineClass",
    "defineHiddenClass",
    "findVirtual",
    "findStatic",
    "findSpecial",
    "findGetter",
    "findSetter",
    "metafactory",
    "unreflect",
}


def analyze_source(src, file="<src>"):
    tree, src_b = parse(src)
    findings = []
    for inv in find(tree.root_node, "method_invocation"):
        nm = inv.child_by_field_name("name")
        if nm is None:
            continue
        name = node_text(nm, src_b)
        if name not in REFLECT:
            continue
        line, col, _, _ = span(inv)
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": f"reflective/proxy/bytecode call '{name}(...)' creates a call-graph edge invisible to static analysis",
                "note": node_text(inv, src_b),
                "help": "prefer a direct, statically-typed call or interface dispatch so the call graph stays analyzable",
                "judge": True,
            }
        )
    return findings

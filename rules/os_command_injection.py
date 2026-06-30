# rule: Flag Runtime.exec/ProcessBuilder invocations whose command or argument array is built from tainted (user/network-controlled) data without sanitization or allowlisting.
# (authored by RuleSmith from the description above)

# rule: Flag Runtime.exec/ProcessBuilder invocations whose command or argument array is built from tainted (user/network-controlled) data without sanitization or allowlisting.
"""Detect OS command injection: exec/ProcessBuilder fed tainted input without sanitization or allowlisting."""

import re
from rulesmith.parse import parse, find, span, node_text

RULE = "os-command-injection"

# tokens that mark a value as user/network controlled
TAINT = (
    "getParameter",
    "getParameterValues",
    "getHeader",
    "getQueryString",
    "getCookies",
    "getInputStream",
    "readLine",
    "getenv",
    "getProperty",
    "args[",
    "getReader",
    "nextLine",
    "getRemoteUser",
    "getRequestURI",
)
# tokens that mark a check/cleanse applied to a value
SANITIZE = (
    "matches",
    "Pattern",
    "allowlist",
    "whitelist",
    "sanitize",
    "escape",
    "validate",
    "contains",
    "equals",
)


def _has(text, toks):
    return any(t in text for t in toks)


def _word(name, text):
    return re.search(r"\b" + re.escape(name) + r"\b", text) is not None


def analyze_source(src, file="<src>"):
    tree, b = parse(src)
    findings = []
    for m in find(tree.root_node, "method_declaration", "constructor_declaration"):
        tainted = set()
        sanitized = set()
        # local vars whose initializer pulls tainted data (and isn't itself cleansed)
        for d in find(m, "local_variable_declaration"):
            t = node_text(d, b)
            for vd in find(d, "variable_declarator"):
                nm = vd.child_by_field_name("name")
                if nm is None:
                    continue
                name = node_text(nm, b)
                if _has(t, TAINT) and not _has(t, SANITIZE):
                    tainted.add(name)
        # guard conditions that validate/allowlist a tainted var
        for cond in find(m, "if_statement"):
            c = cond.child_by_field_name("condition")
            if c is None:
                continue
            ct = node_text(c, b)
            if _has(ct, SANITIZE):
                for name in list(tainted):
                    if _word(name, ct):
                        sanitized.add(name)
        live = tainted - sanitized
        # collect sink calls: Runtime.exec(...), ProcessBuilder.command(...), new ProcessBuilder(...)
        sinks = []
        for inv in find(m, "method_invocation"):
            nm = inv.child_by_field_name("name")
            if nm is not None and node_text(nm, b) in ("exec", "command"):
                a = inv.child_by_field_name("arguments")
                if a is not None:
                    sinks.append((inv, node_text(a, b)))
        for oc in find(m, "object_creation_expression"):
            ty = oc.child_by_field_name("type")
            if ty is not None and node_text(ty, b) == "ProcessBuilder":
                a = oc.child_by_field_name("arguments")
                if a is not None:
                    sinks.append((oc, node_text(a, b)))
        for node, args in sinks:
            hit = _has(args, TAINT) or any(_word(n, args) for n in live)
            if not hit:
                continue
            if _has(args, SANITIZE):
                continue
            line, col, _, _ = span(node)
            findings.append(
                {
                    "rule": RULE,
                    "file": file,
                    "line": line,
                    "col": col,
                    "message": "OS command built from tainted input without sanitization or allowlisting",
                    "note": "argument: " + args.strip(),
                    "help": "Validate against an allowlist of commands/args, or pass args as a fixed array and avoid the shell.",
                    "judge": True,
                }
            )
    return findings

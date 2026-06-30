# rule: Flag long high-Shannon-entropy string literals or known key-format prefixes (AKIA, ghp_, sk_live_) embedded in source as likely leaked API keys or tokens.
# (authored by RuleSmith from the description above)

# rule: flag long high-Shannon-entropy string literals or known key-format prefixes (AKIA, ghp_, sk_live_) embedded in source as likely leaked API keys or tokens

import math

from rulesmith.parse import parse, find, span, node_text

RULE = "high-entropy-secret-literal"

# Known credential format prefixes (AWS access key, GitHub PAT, Stripe live key, etc.)
_PREFIXES = (
    "AKIA",
    "ASIA",
    "ghp_",
    "gho_",
    "ghu_",
    "ghs_",
    "github_pat_",
    "sk_live_",
    "pk_live_",
    "sk-",
    "xoxb-",
    "xoxp-",
    "AIza",
)

_MIN_LEN = 20  # ignore short literals; real secrets are long
_MIN_ENTROPY = 4.0  # bits/char; random base64/hex tokens sit well above this


def _unquote(text):
    # node_text includes the surrounding quotes; strip one matching pair
    if len(text) >= 2 and text[0] in "\"'" and text[-1] == text[0]:
        return text[1:-1]
    return text


def _shannon(s):
    if not s:
        return 0.0
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def analyze_source(src, file="<src>"):
    tree, src_bytes = parse(src)
    findings = []
    for lit in find(tree.root_node, "string_literal"):
        content = _unquote(node_text(lit, src_bytes))
        if not content:
            continue
        prefix = next((p for p in _PREFIXES if content.startswith(p)), None)
        entropy = None
        # entropy path: only opaque token-like blobs (no whitespace), long + high-entropy
        if prefix is None:
            if " " in content or "\t" in content or len(content) < _MIN_LEN:
                continue
            entropy = _shannon(content)
            if entropy < _MIN_ENTROPY:
                continue
        line, col, _el, _ec = span(lit)
        if prefix is not None:
            why = f"matches known key prefix '{prefix}'"
        else:
            why = f"length {len(content)}, Shannon entropy {entropy:.2f} bits/char"
        findings.append(
            {
                "rule": RULE,
                "file": file,
                "line": line,
                "col": col,
                "message": "likely hardcoded API key or token in string literal",
                "note": (content[:12] + "…") + f" ({why})",
                "help": "Move the secret to an env var / secret manager and rotate it; it is exposed in source and git history.",
                "judge": entropy is not None,
            }
        )
    return findings

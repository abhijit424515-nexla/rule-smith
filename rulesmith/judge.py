"""Phase 5: judgment layer. Adjudicate hybrid findings with claude -p.

Deterministic primitives flag candidates; the judge filters the residual
false positives (e.g. a *Reader that is not actually an IO resource) using
the finding's evidence + a code snippet. Verdicts are cached keyed on
(rule, snippet) so the same facts give the same verdict -- pseudo-determinism.
"""
import hashlib
import json
import os

from .llm import complete, extract_json

CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".rulesmith_cache.json")

PROMPT = '''A deterministic static analyzer flagged a potential issue. Decide if it \
is a REAL issue or a false positive. Be strict: only call it real if you are \
confident from the code shown.

rule: {rule}
message: {message}
computed evidence: {note}

code:
```java
{snippet}
```

Common false positives for resource-leak: the type only looks closeable by name \
(e.g. OffsetStorageReader, StreamReader, a DTO) but is not an IO/DB resource that \
owns a handle; or the object is provided/owned by a framework or caller.

Return ONLY JSON: {{"real": true|false, "reason": "<one sentence>"}}'''


def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            return json.load(open(CACHE_PATH))
        except Exception:
            return {}
    return {}


def save_cache(cache):
    json.dump(cache, open(CACHE_PATH, "w"), indent=0)


def _key(rule, snippet):
    return hashlib.sha256((rule + "\n" + snippet).encode("utf8")).hexdigest()[:16]


def snippet_for(src, line, before=3, after=14):
    lines = src.splitlines()
    lo = max(0, line - 1 - before)
    hi = min(len(lines), line + after)
    return "\n".join(lines[lo:hi])


def judge(finding, snippet, cache):
    """Returns {'real': bool, 'reason': str}. Cached by (rule, snippet)."""
    k = _key(finding["rule"], snippet)
    if k in cache:
        return cache[k]
    reply = complete(PROMPT.format(
        rule=finding["rule"], message=finding["message"],
        note=finding.get("note", ""), snippet=snippet))
    try:
        v = extract_json(reply)
        v = {"real": bool(v.get("real")), "reason": str(v.get("reason", ""))}
    except Exception as e:
        v = {"real": True, "reason": f"judge parse error, kept conservatively: {e}"}
    cache[k] = v
    return v

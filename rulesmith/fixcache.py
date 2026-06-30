"""Per-file fix cache at /tmp/rulesmith.cache.

Keyed on (ruleset, full file source, model) -> fixed full source. The file
content is part of the key, so any edit auto-invalidates its entry; --refresh
forces a recompute even when the content is unchanged (e.g. to retry the model).
"""

import hashlib
import json

CACHE_PATH = "/tmp/rulesmith.cache"


def key(rules, src, model):
    payload = json.dumps(
        [sorted(rules) if rules else [], src, model or ""], ensure_ascii=False
    )
    return hashlib.sha256(payload.encode("utf8")).hexdigest()


def load():
    try:
        with open(CACHE_PATH, encoding="utf8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf8") as fh:
            json.dump(cache, fh)
    except OSError:
        pass

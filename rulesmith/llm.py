"""LLM backend via the Claude Code CLI (headless `claude -p`).

No API key required -- uses the user's authenticated Claude Code session.
This is the supported headless interface (same as the Agent SDK).
"""

import json
import subprocess


def complete(prompt, system=None, timeout=300, model=None):
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    if system:
        cmd += ["--append-system-prompt", system]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude -p failed: {r.stderr[:500]}")
    data = json.loads(r.stdout)
    if data.get("is_error"):
        raise RuntimeError(f"claude error: {data.get('result', '')[:500]}")
    return data["result"]


def extract_json(text):
    """Pull the first complete JSON object out of an LLM reply."""
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in reply")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])
    raise ValueError("unbalanced JSON object in reply")

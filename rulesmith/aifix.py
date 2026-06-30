"""AI-assisted fix via the Claude Code CLI (claude -p).

For findings with no deterministic autofix, hand the file + its findings to
claude -p and ask for a minimal, behavior-preserving rewrite. The result is
parse-validated before it is written, so a malformed reply is never applied.
"""

from .llm import complete
from .parse import parse

PROMPT = """You are a precise, surgical code-fixing tool. You are given one Java \
source file and a list of static-analysis findings from RuleSmith. Fix EXACTLY \
those findings and nothing else.

Hard rules:
- Make the MINIMAL change that resolves each listed finding. Change nothing else.
- Preserve behavior, public API, method/field names, ordering, comments, and the \
existing formatting/indentation style. Do not reformat untouched code.
- Do NOT refactor, rename, optimize, add logging, or add comments that were not \
requested by a finding.
- Add an import only if a fix you make requires it; never remove existing imports \
unless a fix makes them unused.
- If a finding cannot be fixed without changing observable behavior or guessing at \
intent, leave that code UNCHANGED rather than risk a wrong fix.
- The file must remain syntactically valid Java: keep the package declaration, \
class structure, and braces intact.

Findings to fix:
{findings}

Output contract:
- Output ONLY the complete corrected file content, from its first line to its last.
- No markdown fences, no diff markers, no commentary before or after.

FILE: {path}
-----8<----- BEGIN FILE -----8<-----
{source}
-----8<----- END FILE -----8<-----"""


def _strip_fences(text):
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        # drop opening fence (``` or ```java) and trailing fence
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines)
    return t


def _findings_block(findings):
    out = []
    for f in findings:
        out.append(
            f"- [{f['rule']}] line {f['line']}:{f.get('col', 1)} — {f['message']}"
            + (f"\n    why: {f['note']}" if f.get("note") else "")
            + (f"\n    hint: {f['help']}" if f.get("help") else "")
        )
    return "\n".join(out)


def ai_fix_file(src, findings, path, timeout=300, model=None):
    """Returns (new_src, ok). ok is False (and new_src is the original) if the
    reply does not parse, so a bad fix is never written."""
    prompt = PROMPT.format(findings=_findings_block(findings), path=path, source=src)
    reply = complete(prompt, timeout=timeout, model=model)
    candidate = _strip_fences(reply)
    if not candidate.strip():
        return src, False
    tree, _ = parse(candidate)
    if tree.root_node.has_error:
        return src, False
    if not candidate.endswith("\n"):
        candidate += "\n"
    return candidate, True

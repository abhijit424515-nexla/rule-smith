"""Rust-style diagnostics: span + note (evidence) + help + doc link."""

_DOC = "https://rules.smith.dev"


def format_finding(f):
    sev = f.get("severity", "warning")
    rule = f["rule"]
    head = f"{sev}[{rule}]: {f['message']}"
    loc = f"  --> {f['file']}:{f['line']}:{f['col']}"
    lines = [head, loc]
    if f.get("note"):
        lines.append(f"   = note: {f['note']}")          # the deterministic evidence
    if f.get("help"):
        lines.append(f"   = help: {f['help']}")
    lines.append(f"   = see:  {_DOC}/{rule}")
    return "\n".join(lines)

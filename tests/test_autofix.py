import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rules.resource_leak import fix_edits, apply_edits, analyze_source
from rulesmith.parse import parse

FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures", "resource_leak")


def run():
    ok = True
    # never-closed, single resource in block -> autofixed, re-analysis clean, parses
    src = open(os.path.join(FIX, "leak_no_close.java")).read()
    edits, skipped = fix_edits(src, "leak_no_close.java")
    assert edits, "expected an autofix edit"
    new = apply_edits(src, edits)
    assert "try (InputStream in = open()) {" in new, "expected try-with-resources wrap"
    tree, _ = parse(new)
    assert not tree.root_node.has_error, "fixed source must parse without errors"
    after = analyze_source(new, "fixed")
    assert len(after) == 0, f"fixed source should be clean, got {len(after)}"
    print("  [ok] leak_no_close autofix: wraps, parses, re-analysis clean")

    # not-closed-on-all-paths -> suggest only, no autofix edit
    src2 = open(os.path.join(FIX, "leak_early_return.java")).read()
    edits2, skipped2 = fix_edits(src2, "leak_early_return.java")
    assert not edits2 and skipped2 == 1, "early-return variant must be suggest-only"
    print("  [ok] leak_early_return: suggest-only (no risky autofix)")

    print("autofix:", "ALL PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)

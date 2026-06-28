import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rules.resource_leak import analyze_source
from rulesmith.report import format_finding

FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures", "resource_leak")
EXPECT = {
    "leak_no_close.java": 1,
    "leak_early_return.java": 1,
    "safe_finally.java": 0,
    "safe_twr.java": 0,
    "safe_escapes.java": 0,
}

def run():
    ok = True
    for fn, exp in EXPECT.items():
        src = open(os.path.join(FIX, fn)).read()
        found = analyze_source(src, fn)
        status = "ok" if len(found) == exp else "FAIL"
        if len(found) != exp:
            ok = False
        print(f"  [{status}] {fn}: {len(found)} findings (expected {exp})")
        for f in found:
            for line in format_finding(f).splitlines():
                print(f"      {line}")
    print("resource-leak fixtures:", "ALL PASS" if ok else "FAILURES")
    return ok

if __name__ == "__main__":
    sys.exit(0 if run() else 1)

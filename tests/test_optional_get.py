import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rules.optional_get import analyze_source

FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures", "optional_get")
EXPECT = {
    "violation_unguarded.java": 1,
    "violation_branch.java": 1,
    "clean_guarded_if.java": 0,
    "clean_early_return.java": 0,
}


def run():
    ok = True
    for fn, exp in EXPECT.items():
        got = len(analyze_source(open(os.path.join(FIX, fn)).read(), fn))
        st = "ok" if got == exp else "FAIL"
        if got != exp:
            ok = False
        print(f"  [{st}] {fn}: {got} (expected {exp})")
    print("optional-get:", "ALL PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)

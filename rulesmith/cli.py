"""rulesmith CLI: lint, lint --fix, list."""
import argparse
import os
import sys
import glob

from rules import resource_leak
from rulesmith.report import format_finding

# rule registry (Phase 2 has one; codegen/authoring fills this later)
RULES = {resource_leak.RULE: resource_leak}


def _java_files(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += [f for f in glob.glob(p + "/**/*.java", recursive=True)
                    if "/target/" not in f]
        elif p.endswith(".java"):
            out.append(p)
    return out


def cmd_list(_args):
    for name, mod in RULES.items():
        print(f"{name:16} {mod.__doc__.strip().splitlines()[0]}")
    return 0


def cmd_lint(args):
    files = _java_files(args.paths)
    total = 0
    fixed = 0
    skipped = 0
    for f in files:
        try:
            src = open(f, encoding="utf8", errors="replace").read()
        except OSError:
            continue
        rel = os.path.relpath(f)
        if args.fix:
            edits, sk = resource_leak.fix_edits(src, rel)
            skipped += sk
            if edits:
                new = resource_leak.apply_edits(src, edits)
                if not args.dry_run:
                    open(f, "w", encoding="utf8").write(new)
                fixed += len(edits) // 2
                print(f"{'would fix' if args.dry_run else 'fixed'} {rel}: "
                      f"{len(edits)//2} resource(s) wrapped in try-with-resources")
        else:
            findings = []
            for mod in RULES.values():
                findings += mod.analyze_source(src, rel)
            total += len(findings)
            for fd in findings:
                print(format_finding(fd))
                print()
    if args.fix:
        print(f"\n{fixed} auto-fixed, {skipped} need manual handling (suggest-only).")
        return 0
    print(f"{total} finding(s) across {len(files)} file(s).")
    return 1 if total else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rulesmith")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list installed rules").set_defaults(fn=cmd_list)
    lp = sub.add_parser("lint", help="lint Java files/dirs")
    lp.add_argument("paths", nargs="+")
    lp.add_argument("--fix", action="store_true", help="apply safe autofixes")
    lp.add_argument("--dry-run", action="store_true", help="with --fix: don't write")
    lp.set_defaults(fn=cmd_lint)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

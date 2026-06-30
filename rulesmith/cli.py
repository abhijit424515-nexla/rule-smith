"""rulesmith CLI: lint, lint --fix, list."""

import argparse
import os
import sys
import glob

import importlib.util
from rulesmith.report import format_finding
from rules import resource_leak

_RULES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules"
)


def discover_rules():
    """Load every rules/*.py module exposing RULE + analyze_source."""
    out = {}
    for fn in sorted(glob.glob(os.path.join(_RULES_DIR, "*.py"))):
        if os.path.basename(fn) == "__init__.py":
            continue
        spec = importlib.util.spec_from_file_location(
            "rule_" + os.path.basename(fn)[:-3], fn
        )
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            continue
        if hasattr(mod, "RULE") and hasattr(mod, "analyze_source"):
            out[mod.RULE] = mod
    return out


RULES = discover_rules()


def _java_files(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += [
                f
                for f in glob.glob(p + "/**/*.java", recursive=True)
                if "/target/" not in f
            ]
        elif p.endswith(".java"):
            out.append(p)
    return out


def cmd_list(_args):
    for name, mod in RULES.items():
        doc = (mod.__doc__ or name).strip().splitlines()[0]
        print(f"{name:16} {doc}")
    return 0


def cmd_lint(args):
    files = _java_files(args.paths)
    _cache = {}
    filtered = []
    if getattr(args, "judge", False):
        from rulesmith import judge as judgemod

        _cache = judgemod.load_cache()
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
            if args.rules and "resource-leak" not in args.rules:
                continue
            edits, sk = resource_leak.fix_edits(src, rel)
            skipped += sk
            if edits:
                new = resource_leak.apply_edits(src, edits)
                if not args.dry_run:
                    open(f, "w", encoding="utf8").write(new)
                fixed += len(edits) // 2
                print(
                    f"{'would fix' if args.dry_run else 'fixed'} {rel}: "
                    f"{len(edits) // 2} resource(s) wrapped in try-with-resources"
                )
        else:
            findings = []
            for name, mod in RULES.items():
                if args.rules and name not in args.rules:
                    continue
                findings += mod.analyze_source(src, rel)
            if args.judge and findings:
                from rulesmith import judge as judgemod

                kept = []
                for fd in findings:
                    if not fd.get("judge"):
                        kept.append(fd)
                        continue
                    snip = judgemod.snippet_for(src, fd["line"])
                    v = judgemod.judge(fd, snip, _cache)
                    if v["real"]:
                        fd["note"] = (
                            fd.get("note", "") + f" | judge: real ({v['reason']})"
                        )
                        kept.append(fd)
                    else:
                        filtered.append((rel, fd, v["reason"]))
                findings = kept
            total += len(findings)
            for fd in findings:
                print(format_finding(fd))
                print()
    if args.fix:
        print(f"\n{fixed} auto-fixed, {skipped} need manual handling (suggest-only).")
        return 0
    if args.judge:
        from rulesmith import judge as judgemod

        judgemod.save_cache(_cache)
        if filtered:
            print(
                f"\n{len(filtered)} finding(s) filtered as false positives by the judge:"
            )
            for rel, fd, reason in filtered:
                print(f"  filtered[{fd['rule']}] {rel}:{fd['line']}: {fd['message']}")
                print(f"     = judge: not a real issue -- {reason}")
            print()
    print(f"{total} finding(s) across {len(files)} file(s).")
    return 1 if total else 0


def cmd_add(args):
    from rulesmith.authoring import add_rule

    rid = add_rule(" ".join(args.description))
    return 0 if rid else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rulesmith")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list installed rules").set_defaults(fn=cmd_list)
    lp = sub.add_parser("lint", help="lint Java files/dirs")
    lp.add_argument("paths", nargs="+")
    lp.add_argument("--fix", action="store_true", help="apply safe autofixes")
    lp.add_argument("--dry-run", action="store_true", help="with --fix: don't write")
    lp.add_argument(
        "--judge",
        action="store_true",
        help="filter hybrid findings via claude -p (cached)",
    )
    lp.add_argument(
        "--rules",
        type=lambda x: set(x.split(",")),
        default=None,
        help="comma-separated rule ids to run",
    )
    lp.set_defaults(fn=cmd_lint)
    ad = sub.add_parser("add", help="compile an English rule into a checked rule")
    ad.add_argument("description", nargs="+", help="the rule in plain English")
    ad.set_defaults(fn=cmd_add)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

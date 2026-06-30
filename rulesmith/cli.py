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


def _analyze(src, rel, rules):
    out = []
    for name, mod in RULES.items():
        if rules and name not in rules:
            continue
        out += mod.analyze_source(src, rel)
    return out


def _print_diff(before, after, path):
    import difflib
    import sys

    tty = sys.stdout.isatty()
    R, G, C, Z = (
        ("\033[31m", "\033[32m", "\033[36m", "\033[0m") if tty else ("", "", "", "")
    )
    for line in difflib.unified_diff(
        before.splitlines(), after.splitlines(), fromfile=path, tofile=path, lineterm=""
    ):
        if line.startswith("+++") or line.startswith("---"):
            print(line)
        elif line.startswith("+"):
            print(f"{G}{line}{Z}")
        elif line.startswith("-"):
            print(f"{R}{line}{Z}")
        elif line.startswith("@@"):
            print(f"{C}{line}{Z}")
        else:
            print(line)


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
    auto_fixed = 0
    ai_fixed = 0
    cached_hits = 0
    _fixcache = {}
    if args.fix:
        from rulesmith import fixcache

        _fixcache = fixcache.load()
    for f in files:
        try:
            src = open(f, encoding="utf8", errors="replace").read()
        except OSError:
            continue
        rel = os.path.relpath(f)
        # always analyze, so the finding count is honest regardless of --fix
        findings = _analyze(src, rel, args.rules)
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
                    fd["note"] = fd.get("note", "") + f" | judge: real ({v['reason']})"
                    kept.append(fd)
                else:
                    filtered.append((rel, fd, v["reason"]))
            findings = kept
        total += len(findings)

        if args.fix:
            from rulesmith import fixcache

            before = src
            ck = fixcache.key(args.rules, before, args.model)
            if args.refresh_cache:
                _fixcache.pop(ck, None)
            if ck in _fixcache:
                src = _fixcache[ck]
                if src != before:
                    cached_hits += 1
            else:
                # deterministic codemod first (resource-leak only), AI-free
                edits, _ = resource_leak.fix_edits(src, rel)
                if edits:
                    src = resource_leak.apply_edits(src, edits)
                    auto_fixed += len(edits) // 2
                # AI-fix whatever the codemod could not fix (skip if --model none)
                if args.model and args.model.lower() != "none":
                    remaining = _analyze(src, rel, args.rules)
                    if remaining:
                        from rulesmith import aifix

                        new_src, ok = aifix.ai_fix_file(
                            src, remaining, rel, model=args.model
                        )
                        if ok and new_src != src:
                            src = new_src
                            ai_fixed += 1
                        elif not ok:
                            print(f"ai-fix skipped {rel}: reply did not parse")
                _fixcache[ck] = src
            if src != before:
                _print_diff(before, src, rel)
                if not args.dry_run:
                    open(f, "w", encoding="utf8").write(src)
        else:
            for fd in findings:
                print(format_finding(fd))
                print()

    if args.fix:
        from rulesmith import fixcache

        fixcache.save(_fixcache)
        verb = "would fix" if args.dry_run else "fixed"
        parts = [f"{total} finding(s)", f"{auto_fixed} auto-fixed"]
        if args.model and args.model.lower() != "none":
            parts.append(f"{ai_fixed} file(s) ai-fixed ({args.model})")
        if cached_hits:
            parts.append(f"{cached_hits} from cache")
        print(f"\n{verb}: " + ", ".join(parts) + ".")
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

    rid = add_rule(" ".join(args.description), model=args.model)
    return 0 if rid else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rulesmith")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list installed rules").set_defaults(fn=cmd_list)
    lp = sub.add_parser("lint", help="lint Java files/dirs")
    lp.add_argument("paths", nargs="+")
    lp.add_argument(
        "--fix",
        action="store_true",
        help="fix in place (deterministic; add --model to AI-fix the rest)",
    )
    lp.add_argument(
        "--dry-run", action="store_true", help="with --fix: show the diff, do not write"
    )
    lp.add_argument(
        "--model",
        default="sonnet",
        help="with --fix: model to AI-fix the residual via claude -p (default: sonnet; 'none' = deterministic only)",
    )
    lp.add_argument(
        "--refresh-cache",
        action="store_true",
        help="with --fix: ignore any cached fix for the given files and recompute",
    )
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
    ad.add_argument(
        "--model", default=None, help="claude model for codegen (e.g. opus, sonnet)"
    )
    ad.set_defaults(fn=cmd_add)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

# Walkthrough — fixing a messy codebase one rule at a time

`examples/java/` has two realistic files with **6 issues across all 6 installed
rules**. `examples/java-fixed/` is the same code after every fix (lints clean).
This page shows the progression.

```
alias rulesmith='python -m rulesmith.cli'
```

## Step 0 — see everything that's wrong
```
$ rulesmith lint examples/java
warning[resource-leak]:            `out` (FileOutputStream) is never closed        ReportWriter.java
warning[string-equality-check]:    Use .equals() to compare strings, not '=='      ReportWriter.java
warning[empty-catch-block]:        Empty catch block swallows exception            ReportWriter.java
warning[optional-get-without-ispresent]: `name.get()` is not guarded               OrderProcessor.java
warning[enum-switch-default]:      Switch over enum must have a default case        OrderProcessor.java
warning[boxed-integer-long-comparison]: Boxed Integer/Long compared with ==         OrderProcessor.java
6 finding(s) across 2 file(s).
```

## Step 1 — auto-fix what is safe (resource-leak)
Only the provably-safe subset auto-rewrites. Here, one resource:
```
$ rulesmith lint --fix examples/java
fixed examples/java/ReportWriter.java: 1 resource(s) wrapped in try-with-resources
1 auto-fixed, 0 need manual handling (suggest-only).
```
```diff
- FileOutputStream out = newStream(path);
- out.write(data);
+ try (FileOutputStream out = newStream(path)) {
+     out.write(data);
+ }
```
(try-with-resources closes on every exit — normal or exception. google-java-format
reflows the indentation afterward.)

## Steps 2-6 — the suggest-only rules (you apply the fix the diagnostic names)

| # | Rule | Before | After |
|---|------|--------|-------|
| 2 | string-equality-check | `format == "csv"` | `format.equals("csv")` |
| 3 | empty-catch-block | `catch (IOException e) {}` | `catch (IOException e) { throw new RuntimeException(e); }` |
| 4 | enum-switch-default | switch with no default | add `default: return "unknown";` |
| 5 | optional-get-without-ispresent | `return name.get();` | `return name.orElse("anonymous");` |
| 6 | boxed-integer-long-comparison | `return a == b;` | `return a.equals(b);` |

Each diagnostic carries the fix in its `= help:` line and a `= note:` with the
deterministic evidence (e.g. for the leak: "close() is on no path").

## Done — clean
```
$ rulesmith lint examples/java-fixed
0 finding(s) across 2 file(s).
```

## Try the judge on a real repo
The name-based resource heuristic can over-flag (e.g. `OffsetStorageReader`).
`--judge` adjudicates the residual via `claude -p` (cached):
```
rulesmith lint --judge <real-java-dir>
```

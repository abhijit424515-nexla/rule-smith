# Walkthrough — flow-sensitive bugs a CLAUDE.md can't catch

`examples/java/PaymentGateway.java` has ten methods. Each is syntactically
ordinary — the defect lives in the control or data flow. A prose rule in a
CLAUDE.md is read by an LLM matching text; it has no CFG, so it cannot decide
"is close() on every path?" or "does the null-check dominate this deref?".
RuleSmith runs the actual analysis.

```
alias rulesmith='python -m rulesmith.cli'
TEN=resource-leak,optional-get-without-ispresent,null-deref-needs-dominating-guard,unchecked-downcast,field-read-before-assign,non-atomic-shared-update,guarded-by-lock-held,no-string-concat-in-loop,no-superfluous-else,constructor-definite-assignment
```

## The ten checks (each flow-sensitive)

| # | Rule | Why a text rule misses it |
|---|------|----------------------------|
| 1 | field-read-before-assign | field read before its assignment *in the ctor* |
| 2 | resource-leak | close() exists, but an early `return` skips it on one path |
| 3 | optional-get-without-ispresent | get() not *dominated* by isPresent() |
| 4 | null-deref-needs-dominating-guard | guard misses one path to the deref |
| 5 | unchecked-downcast | cast not *dominated* by an instanceof |
| 6 | non-atomic-shared-update | read-modify-write on a @GuardedBy field |
| 7 | guarded-by-lock-held | @GuardedBy field touched without the lock |
| 8 | no-string-concat-in-loop | += inside a loop (O(n^2)) |
| 9 | no-superfluous-else | else after a branch that always returns |
| 10 | constructor-definite-assignment | field not assigned on every ctor path |

## Step 0 — see the flow bugs
```
$ rulesmith lint --rules $TEN examples/java
... 12 findings (the ten rules; guarded-by fires on two accesses)
```
Each finding's `= note:` states the graph fact (post-dominance, dominance,
definite-assignment) — deterministic, reproducible.

## Step 1 — repair the flow, not the syntax
`examples/java-fixed/PaymentGateway.java` is the same code with the control flow
fixed: try-with-resources, orElse, a dominating instanceof, synchronized access,
StringBuilder, no else-after-return.
```
$ rulesmith lint --rules $TEN examples/java-fixed
0 finding(s)
```

The verdict flipped on the **flow**. A CLAUDE.md rule sees near-identical code in
both files and can't tell them apart — that's the value RuleSmith adds that you
can't abstract away with "just put it in CLAUDE.md."

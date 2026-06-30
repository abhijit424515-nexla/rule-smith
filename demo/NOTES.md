# RuleSmith — demo day script

~7 min. Goal: show *why a CLAUDE.md full of rules is not enough*, and how
RuleSmith delivers the value you can't vibe out of a prose rulebook — (1) it
catches flow-sensitive bugs a CLAUDE.md cannot, (2) findings are deterministic
with cited graph evidence, (3) it writes its own rules from English, gated by
tests, (4) it filters its own false positives. Terminal in the repo, venv active.
Record a fallback video of the `add` beat (it calls claude -p, network-dependent).

Setup (once, off-screen):
```
cd ~/workspace/experiments/rule-smith && source .venv/bin/activate
BC=~/Desktop/clones/backend-connectors
TEN=resource-leak,optional-get-without-ispresent,null-deref-needs-dominating-guard,unchecked-downcast,field-read-before-assign,non-atomic-shared-update,guarded-by-lock-held,no-string-concat-in-loop,no-superfluous-else,constructor-definite-assignment
```

---

## Beat 0 — the trap everyone falls into (45s, no terminal)
Small team, no time to police architecture. The reflex: write the rules into
CLAUDE.md and let the AI handle it. That fails in a way that's easy to miss. A
CLAUDE.md rule is *prose read by an LLM that pattern-matches text* — it has no
control-flow graph, so it can't answer "is close() on *every* path?" or "does the
null-check *dominate* this deref?". Same tokens, different flow: bug here, fine
there. You cannot vibe that out of a sentence. RuleSmith runs the actual CFG +
dominance analysis, deterministically.

## Beat 1 — what CLAUDE.md can't see (110s)  ← the core argument
`examples/java/PaymentGateway.java` is ten methods that each look ordinary
line-by-line. Read two aloud — the leak with an early `return`, the `Optional.get()`
after a branch. "Would you catch these in review? Would a prose rule?"
```
rulesmith lint --rules $TEN examples/java
```
Ten flow-sensitive findings, each with a `= note:` stating the graph fact
(post-dominance, dominance, definite-assignment). Then the payoff:
```
rulesmith lint --rules $TEN examples/java-fixed
# 0 findings
```
Same shapes, repaired control flow → clean. Talking point: the verdict flipped on
the *flow*, not the syntax. A CLAUDE.md rule sees identical-looking code and can't
tell the two apart. This is the value you can't abstract away with "just put it in
CLAUDE.md."

## Beat 2 — it's a real bug, in real code (75s)
```
rulesmith lint --rules resource-leak $BC/one-drive-probe-service/src/main/java/com/nexla/probe/onedrive/OneDriveConnectorService.java
```
Point at the FileInputStream finding. The `= note:` is deterministic evidence —
post-dominance says close() is on no path. Not a vibe; a graph fact, reproducible
every run.

## Beat 3 — author a NEW rule in English, live (90s)
```
rulesmith add "a switch over an enum must have a default case"
```
Watch: claude -p compiles it to a python rule + pos/neg fixtures, the fixture gate
runs, it installs only on green. Talking point: the LLM writes the rule, but a
deterministic test gate decides if it ships — *that* is why you can trust it, and
it's exactly the gate a CLAUDE.md rule never gets. (Fallback: play recording.)

## Beat 4 — it filters its own false positives (75s)
```
rulesmith lint --rules resource-leak $BC/kafka-connect-iceberg-source/src/main/java/com/nexla/connector/iceberg/source/IcebergSourceTask.java
rulesmith lint --rules resource-leak --judge $BC/kafka-connect-iceberg-source/src/main/java/com/nexla/connector/iceberg/source/IcebergSourceTask.java
```
First: OffsetStorageReader flagged (name heuristic). Second: judge filters it,
"not an IO resource". Talking point: primitives are conservative on purpose;
Claude adjudicates the residual, verdict cached so it's reproducible.

## Beat 5 — fix it (45s)
```
rulesmith lint --fix --dry-run $BC/<a-leak-file>.java
```
Show the try-with-resources rewrite. Only the provably-safe subset auto-fixes; the
rest stays a suggestion. rustc-style help + doc link on every finding.

## Close (30s)
The argument, in one line: CLAUDE.md is a rulebook an LLM *reads*; RuleSmith is a
rulebook a deterministic engine *runs*. 113 rules implemented (184-rule catalog
mined from Checker Framework, Effective Java, NASA Power of Ten, OWASP, FP
literature). Built on tree-sitter + CFG/dominance + claude -p. One CLI, no API key.

---

## Cheat sheet — exact things to point at
- 10 flow-sensitive rules: `examples/java/PaymentGateway.java` (12 findings) vs
  `examples/java-fixed/PaymentGateway.java` (0) — same shapes, different flow.
- Real leak: OneDriveConnectorService.java:516 `fileInput` (FileInputStream).
- False positive filtered by --judge: IcebergSourceTask.java `reader` (OffsetStorageReader).
- Walkthrough of a simpler messy file: `examples/WALKTHROUGH.md`.

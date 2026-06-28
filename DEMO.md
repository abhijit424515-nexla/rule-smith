# RuleSmith — demo day script

~6 min. Goal: prove the four claims judges will doubt — (1) it writes its own
rules from English, (2) findings are deterministic with cited evidence, (3) it
finds real bugs, (4) it filters its own false positives. Have a terminal in the
repo with the venv active. Record a fallback video of beat 2 (it calls claude -p,
network-dependent).

Setup (once, off-screen):
```
cd ~/workspace/experiments/rule-smith && source .venv/bin/activate
BC=~/Desktop/clones/backend-connectors
```

---

## Beat 0 — the problem (30s, no terminal)
Small teams can't police their own architecture by hand. A CLAUDE.md of rules is
passive — nothing enforces it. SonarQube/Semgrep exist but you can't *describe* a
rule in English and you don't trust AI to lint deterministically. RuleSmith:
deterministic primitives compute the facts, Claude only judges the fuzzy residual.

## Beat 1 — it ships with real rules (45s)
```
rulesmith list
```
Talking point: 184-rule catalog mined from Checker Framework, Effective Java,
NASA Power of Ten, OWASP, FP literature — 104 deterministic. Three families
already installed (detective-CFG, prescriptive-AST).

## Beat 2 — author a NEW rule in English, live (90s)  ← the money shot
```
rulesmith add "a switch over an enum must have a default case"
```
Watch: claude -p compiles it to a python rule + pos/neg fixtures, the fixture
gate runs, it installs only on green. Talking point: "the LLM wrote the rule, but
a deterministic test gate decides if it ships — that's why you can trust it."
(Fallback: play recording if the network stalls.)

## Beat 3 — find a REAL bug, deterministically (90s)
```
rulesmith lint $BC/one-drive-probe-service/src/main/java/com/nexla/probe/onedrive/OneDriveConnectorService.java
```
Point at the FileInputStream finding. Talking point: this is a real leak in
production code. The `= note:` line is the deterministic evidence — post-dominance
says close() is on no path. Not a vibe; a graph fact.

## Beat 4 — it filters its own false positives (75s)
```
rulesmith lint $BC/kafka-connect-iceberg-source/src/main/java/com/nexla/connector/iceberg/source/IcebergSourceTask.java
rulesmith lint --judge $BC/kafka-connect-iceberg-source/src/main/java/com/nexla/connector/iceberg/source/IcebergSourceTask.java
```
First: OffsetStorageReader flagged (name heuristic). Second: judge filters it,
"not an IO resource". Talking point: primitives are conservative on purpose;
Claude adjudicates the residual, verdict cached so it's reproducible.

## Beat 5 — fix it (45s)
```
rulesmith lint --fix --dry-run $BC/<a-leak-file>.java
```
Show the try-with-resources rewrite. Talking point: only the provably-safe subset
auto-fixes; the rest stays a suggestion. rustc-style help + doc link on every one.

## Close (30s)
The table: who writes rules? (catalog + `add`). Deterministic? (graph evidence).
Real bugs? (the leak). Noisy? (judge filters). Built in a weekend on tree-sitter +
dominance + `claude -p`. One CLI, no API key.

---

## Cheat sheet — exact findings to point at
- Real leak: OneDriveConnectorService.java:516 `fileInput` (FileInputStream)
- Real leak: OneDriveConnectorService.java:392 `outputStream`
- False positive: IcebergSourceTask.java:101 `reader` (OffsetStorageReader)
- Whole-repo: 1242 files, 0 parse errors, 78 leak findings, 20 optional-get

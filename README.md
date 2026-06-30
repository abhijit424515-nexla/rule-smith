# RuleSmith

**A coding rulebook a machine *runs* — not one an LLM *reads*.**

You pasted your conventions into a `CLAUDE.md` and hoped the AI would enforce them.
But a `CLAUDE.md` rule is prose pattern-matched by a language model. It has no
control-flow graph, so it cannot answer the questions that actually catch bugs:

> *Is `close()` on **every** path, including the early `return`?*
> *Does the null-check **dominate** this dereference?*

RuleSmith can, because every check runs a real **CFG + dominance** analysis. You
describe a rule in plain English; it compiles to a tested, deterministic check and
installs it into your CLI. **113 rules** ship today, mined from Checker Framework,
Effective Java, NASA's Power of Ten, OWASP, and the FP literature.

---

## Same code. Different flow. Opposite verdict.

```java
// examples/java/PaymentGateway.java          // examples/java-fixed/PaymentGateway.java
InputStream in = open();                       try (InputStream in = open()) {
if (dryRun) return;   // <-- leaks 'in'          if (dryRun) return;   // closed anyway
in.close();                                      use(in);
                                               }
```

```console
$ rulesmith lint --rules resource-leak examples/java
warning[resource-leak]: `in` (InputStream) is never closed
  --> PaymentGateway.java:30
   = note: close() is on no path (post-dominance); resource does not escape
   = help: use try-with-resources

$ rulesmith lint --rules resource-leak examples/java-fixed
0 findings
```

A `CLAUDE.md` rule sees near-identical code in both files and can't tell them apart.
RuleSmith's verdict flipped on the **flow**, not the syntax. That's the value you
can't vibe out of a sentence.

## It finds real bugs, in shipped code

```console
$ rulesmith lint --rules resource-leak \
    backend-connectors/.../onedrive/OneDriveConnectorService.java
warning[resource-leak]: `fileInput` (FileInputStream) is never closed  --> :516
```
Confirmed leak in production. Whole-repo run: **1242 files, 0 parse errors.**
Every finding cites the graph fact behind it — reproducible every run, no AI.

---

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                      # exposes the `rulesmith` command

rulesmith list                        # the 113 installed rules
rulesmith lint path/to/src            # exit 1 on findings (CI-ready)
rulesmith lint --fix path/to/src      # deterministic try-with-resources rewrite
rulesmith add "a switch over an enum must have a default case"
```

## Author a rule in English — and trust it

```console
$ rulesmith add "do not catch NullPointerException; fix the root cause"
[attempt 1] compiling rule via claude -p...
[ok] violation.java: 1   [ok] clean.java: 0   installed 'no-catch-npe' (all green)
```

`claude -p` writes the rule **and** its pos/neg fixtures; a deterministic gate runs
them and installs **only on green**. The LLM proposes; the test gate decides. That
gate is exactly what a `CLAUDE.md` rule never gets.

## AI builds the checks. Code runs them.

| Action | Needs Claude? | Why |
|--------|:---:|-----|
| `lint` · `list` · `--fix` · CI gate | **No** | pure CFG + AST, deterministic, offline, no key |
| `add "<english>"` | **Once** | codegen, then gated by fixtures |
| `lint --judge` | **Cached** | adjudicate a false positive, then cached → AI-free |

The everyday workflow runs forever with no API key. Claude is touched only to
*author* a rule and (optionally) to *adjudicate* a borderline finding — both gated,
both cached by `(rule, snippet)` so the same code always gets the same verdict.

## How it works

![RuleSmith architecture](diagram/ARCHITECTURE.svg)

Deterministic primitives (`parse → cfg → dominance → escape`) compute the
expensive-to-be-wrong facts. Two rule families ride them: **detective** rules
(find bugs, CFG-driven) and **prescriptive** rules (conventions, AST + codemod).
Claude only adjudicates the fuzzy residual.

```
rulesmith/   the engine — parse, cfg (CFG+dominance), dataflow, report, cli, llm, authoring, judge
rules/       113 installed rule modules, each headed by its exact English description
fixtures/    pos/neg test cases per rule — the trust mechanism
examples/    PaymentGateway before/after, real-world/ (5 production files), WALKTHROUGH
demo/        NOTES.md (MARP deck: why CLAUDE.md isn't enough) + rendered slides
diagram/     architecture (excalidraw source + svg)
```

## What it catches

113 rules across null-safety, resource lifecycle, concurrency & locking,
immutability/purity, error handling, type design, security (weak crypto, hardcoded
secrets, broken trust managers), complexity metrics, and naming. Highlights — the
flow-sensitive ones no text rule can see:

`resource-leak` · `optional-get-without-ispresent` · `null-deref-needs-dominating-guard`
· `unchecked-downcast` · `field-read-before-assign` · `non-atomic-shared-update`
· `guarded-by-lock-held` · `constructor-definite-assignment`

See `examples/real-world/` for five unmodified backend-connectors files, each
lighting up 13–15 rules.

## Honest limits

- Resource detection is name-based (no type resolution) → false positives like
  `OffsetStorageReader`. `--judge` filters them via `claude -p`, cached.
- CFG exception edges are coarse (entry-level, not per-statement).
- Autofix covers only `resource-leak`'s provably-safe subset; the other 112 rules
  emit a `= help:` suggestion you apply yourself. The tool never AI-rewrites code.
- Formatting reflow is delegated to google-java-format.

---

*Built on tree-sitter + CFG/dominance + `claude -p`. One CLI, no API key.*

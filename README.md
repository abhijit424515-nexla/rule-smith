# RuleSmith

**A coding rulebook a machine *runs* — not one an LLM *reads*.**

You pasted your conventions into `CLAUDE.md` and hoped the AI would honor them. But a `CLAUDE.md` rule is prose pattern-matched by a language model — no control-flow graph, no call graph, no notion of lock state. RuleSmith compiles an English rule into a tested, deterministic check that runs every time, offline, no API key.

```console
$ rulesmith lint --rules atomic-get-set-race \
    backend-connectors/.../pdf/strategy/DefaultStrategy.java
warning[atomic-get-set-race]: Non-atomic get-then-set on Atomic 'textBB' loses concurrent updates.
  --> DefaultStrategy.java:69:13
   = note: value passed to set() is computed from get(); another thread can update between
   = help: use textBB.updateAndGet(...) or compareAndSet(...)
```

A lost-update race in shipped code. SonarQube doesn't flag it; a `CLAUDE.md` rule can't express it. It needs to see that the written value is **derived from a prior read of the same atomic** — dataflow, not text.

---

## See it

**Same code, different flow, opposite verdict** — `examples/java/PaymentGateway.java`, five defects no syntax rule sees:

```console
$ rulesmith lint --rules $FIVE examples/java | grep warning
warning[blocking-call-while-holding-lock]: fut.get() blocks until the Future completes while holding a lock.
warning[builder-terminal-before-setters]: Builder 'b' is finalized by 'build()' before setter 'total()' runs on it.
warning[guarded-by-lock-held]: Access to @GuardedBy("lock") field 'balance' without holding lock lock.
warning[lambda-captures-mutable-state]: Lambda mutates captured array 'acc'.
warning[pure-method-no-side-effects]: pure method calls a known-impure (mutating) method

$ rulesmith lint --rules $FIVE examples/java-fixed
0 finding(s) across 1 file(s).
```

**A real leak, deterministically** — whole-repo run was 1242 files, 0 parse errors:

```console
$ rulesmith lint --rules resource-leak \
    backend-connectors/.../onedrive/OneDriveConnectorService.java
warning[resource-leak]: `outputStream` (OutputStream) is never closed  --> :392:5
   = note: no close() call found and the resource does not escape the method
   = help: close it in a finally block, or use try-with-resources
```

**Author a rule in English** — the LLM writes it, a fixture gate decides if it ships:

```console
$ rulesmith add "a switch over an enum must have a default case"
[attempt 1] compiling rule via claude -p...
[ok] violation.java: 1   [ok] clean.java: 0   installed 'enum-switch-default' (all green)
```

**Fix it** — deterministic codemod first, AI-fix the residual, colored diff in your terminal:

```console
$ rulesmith lint --fix --dry-run --rules resource-leak \
    backend-connectors/.../onedrive/OneDriveConnectorService.java
would fix .../OneDriveConnectorService.java: 2 resource(s) wrapped in try-with-resources

2 finding(s), 2 auto-fixed.
```

---

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                                  # exposes the `rulesmith` command

rulesmith list                                    # the 114 installed rules
rulesmith lint path/to/src                        # exit 1 on findings (CI-ready)
rulesmith lint --fix path/to/src                  # codemod + AI-fix the rest (sonnet), shows a diff
rulesmith lint --fix --model none path/to/src     # deterministic only, no AI
rulesmith lint --fix --model opus path/to/src     # AI-fix the residual with opus
rulesmith add "a switch over an enum must have a default case"
```

---

## How does it work?

![RuleSmith architecture](diagram/ARCHITECTURE.svg)

Deterministic primitives (`parse → cfg → dominance → escape`) compute the facts that are expensive to get wrong. Two rule families ride them: **detective** rules find bugs (CFG-driven), **prescriptive** rules enforce conventions (AST + codemod). Claude is touched only to *author* a rule and (optionally) to *adjudicate* a borderline finding — both gated, both cached by `(rule, snippet)`, so the same code always gets the same verdict.

| Action | Needs Claude? | Why |
|--------|:---:|-----|
| `lint` · `list` · CI gate | **No** | pure CFG + AST, deterministic, offline |
| `lint --fix` | **Default sonnet** | deterministic codemod, then AI-fix the residual (`--model none` to disable) |
| `add "<english>"` | **Once** | codegen, then gated by fixtures |
| `lint --judge` | **Cached** | adjudicate a false positive, then cached → AI-free |

The trust mechanism for `add`: `claude -p` writes the rule **and** its pos/neg fixtures; a deterministic gate runs them and installs **only on green**. The LLM proposes; the test gate decides. That gate is exactly what a `CLAUDE.md` rule never gets.

## How is it better?

A `CLAUDE.md` rule is *read* by a model on every prompt — fuzzy, unenforced, no flow analysis. RuleSmith is *run* by a deterministic engine — same input, same verdict, citing the graph fact behind it.

And it catches what the textbook linters structurally cannot. **114 rules** mined from Checker Framework, Effective Java, NASA's Power of Ten, OWASP, and the FP literature, including the flow-sensitive ones SonarQube and PMD don't ship:

`builder-terminal-before-setters` (typestate) · `atomic-get-set-race` · `guarded-by-lock-held` · `blocking-call-while-holding-lock` (deadlock) · `pure-method-no-side-effects` (purity via call graph) · `command-query-separation` · `tell-dont-ask` · `lambda-captures-mutable-state` · `local-throw-catch-control-flow` · `null-deref-needs-dominating-guard`

These need a real CFG, call graph, and dataflow — not pattern-matching. See `examples/real-world/` for five unmodified backend-connectors files, each lighting up 13–15 rules.

---

## Repo layout

```
rulesmith/   the engine — parse, cfg (CFG+dominance), dataflow, report, cli, llm, authoring, judge
rules/       114 installed rule modules, each headed by its exact English description
fixtures/    pos/neg test cases per rule — the trust mechanism
examples/    PaymentGateway before/after, real-world/ (5 production files), WALKTHROUGH
demo/        NOTES.md (MARP deck: why CLAUDE.md isn't enough) + rendered slides
diagram/     architecture (excalidraw source + svg)
```

## Honest limits

- Resource detection is name-based (no type resolution) → false positives like `OffsetStorageReader`. `--judge` filters them via `claude -p`, cached.
- CFG exception edges are coarse (entry-level, not per-statement).
- Deterministic autofix covers only `resource-leak`'s provably-safe subset; the other 113 rules emit a `= help:` suggestion. `--fix` applies the codemod and then AI-fixes the residual via claude -p (default sonnet, parse-validated, colored diff); pass `--model none` to stay fully deterministic.
- `--fix` results are cached at `/tmp/rulesmith.cache` keyed on (rules, file content, model); editing the file auto-invalidates, or pass `--refresh-cache`.
- Formatting reflow is delegated to google-java-format.


## The interesting part: where this can go

Today's 114 rules barely scratch what the substrate allows. Once you have a CFG, dominance, a call graph, and def-use chains, a whole class of properties stops being a "hard AI problem" and becomes a *graph query* — decidable, reproducible, fast. Every powerful rule has the same shape: **a question about paths, not about text.**

- *Typestate* — "open before read", "lock before touch", "no use after close": reachability over the CFG.
- *Must-before / must-after* — dominance and post-dominance give you init-before-use, validate-before-trust, acquire-before-release from two graph relations.
- *Taint* — "does untrusted input reach a sink unsanitized?" is a path search: SQLi, traversal, secret-to-network, same traversal.
- *Effect & purity* — the call graph already knows what a method transitively touches: "pure stays pure", "no I/O under this lock".
- *Concurrency* — lock-state is a dataflow fact; out fall guarded-access, lock-ordering, check-then-act races.

The honest limits above are *engineering* gaps (heuristics, coarse exception edges), not *theoretical* ones — the ceiling isn't the analysis, it's how many English sentences you bother to compile. That's the bet: **the hard part was never inventing the check, it was knowing which to write.** RuleSmith makes that a sentence; the graph does the rest.

---

*Built on tree-sitter + CFG/dominance + `claude -p`. One CLI, no API key.*

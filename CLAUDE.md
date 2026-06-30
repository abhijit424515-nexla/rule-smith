# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

RuleSmith compiles an English coding rule into a **deterministic, tested check** that runs offline (no API key) over Java source via tree-sitter. The thesis: a `CLAUDE.md`-style prose rule is pattern-matched by an LLM with no CFG/call-graph/lock-state awareness; RuleSmith runs the same input → same verdict, citing the graph fact behind it.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                        # exposes the `rulesmith` console script

rulesmith list                          # all installed rules + their English description
rulesmith lint <path>                   # lint a file/dir; exit 1 on findings (CI gate)
rulesmith lint --rules a,b <path>       # only named rules (kebab-case ids)
rulesmith lint --fix <path>             # deterministic codemod, then AI-fix residual (default sonnet)
rulesmith lint --fix --model none <p>   # deterministic only, no Claude
rulesmith lint --fix --dry-run <p>      # show colored diff, don't write
rulesmith lint --judge <path>           # filter hybrid findings (judge=True) via claude -p, cached
rulesmith add "<english rule>"          # codegen a new rule, gated by generated fixtures

# tests are standalone scripts (NOT pytest), each with a run() and __main__:
python tests/test_resource_leak.py      # exits 0/1
python tests/test_autofix.py
python tests/test_optional_get.py

pre-commit run --all-files              # ruff (py3.11) + google-java-format (system binary)
```

There is no all-rules test runner. Per-rule fixtures live in `fixtures/<rule_id>/` and are the trust mechanism, but only the three rules above have hand-written `tests/test_*.py`. `add` runs a rule's generated fixtures as an install gate inline.

## Architecture

Two layers. **Deterministic primitives** in `rulesmith/` compute the expensive facts; **rule modules** in `rules/` are thin queries over them. Claude is touched only to *author* a rule (`add`) or *adjudicate*/*fix* a finding (`--judge`/`--fix`) — never for plain `lint`.

Primitive stack (a rule imports these; never reimplement parsing):
- `parse.py` — `parse(src) → (tree, src_bytes)`, plus `find(node, *types)`, `node_text`, `span` (1-based), `walk`, `query`. tree-sitter-java.
- `cfg.py` — `build_method(method_ts, src_b) → CFG`; `dominators`/`postdominators`; `dominates`/`postdominates(a_id, b_id)`. CFG nodes wrap tree-sitter statements. Exception edges are coarse (entry-level, not per-statement).
- `dataflow.py` — `escapes(method_ts, name) → bool` (ownership left the method), `defs_uses(method_ts, name)`.
- `report.py` — `format_finding(dict)` → the `warning[rule]: … --> file:line:col / = note / = help` text.

The full primitive contract Claude must follow when authoring is the `API` string in `authoring.py` — keep it in sync with the actual exports if you change a signature.

### Rule module contract

Every `rules/*.py` (except `__init__.py`) that defines both `RULE` and `analyze_source` is auto-discovered by `cli.discover_rules()` (glob + import; import errors are silently skipped). Contract:

```python
RULE = "kebab-case-id"                              # also the --rules selector and fixtures/ dir (underscored)
def analyze_source(src, file="<src>") -> list[dict] # dict: rule,file,line,col,message,note,help
```

- The module's **first line is a `# rule: <english>` comment** = the exact English spec; `list` prints the module docstring's first line.
- A finding may set `judge=True` to mark it as a heuristic candidate that `--judge` can filter via Claude (cached by `(rule, snippet)`).
- File naming: `rules/<rule_id_with_underscores>.py`, fixtures at `fixtures/<rule_id_with_underscores>/`.

### Detective vs prescriptive

- **Detective** rules find bugs via CFG/dominance/escape/dataflow (e.g. `resource_leak.py` — the flagship; composes CFG + post-dominance + escape). These are the rules SonarQube/PMD can't express.
- **Prescriptive** rules enforce conventions via AST shape (naming, `final`, etc.); some carry a codemod.

### Claude integration (`llm.py`)

All LLM calls go through `complete(prompt, model=...)` which shells out to `claude -p … --output-format json` — uses the user's authenticated Claude Code session, **no API key**. `extract_json` pulls the first balanced `{…}` from the reply.

- `authoring.py` (`add`) — prompts Claude for `{rule_id, module, fixtures}`, writes the module to a tmp file, runs the pos/neg fixtures as a gate, **installs only on green**, retries once with the failure report fed back. The LLM proposes; the fixture gate decides.
- `judge.py` (`--judge`) — adjudicates a `judge=True` finding as real/false-positive, cached.
- `aifix.py` (`--fix`) — after the deterministic codemod, asks Claude to fix the residual; reply is parse-validated before write.
- `fixcache.py` — `--fix` results cached at `/tmp/rulesmith.cache` keyed on `(rules, file content, model)`; editing a file auto-invalidates, or pass `--refresh-cache`.

## Constraints worth knowing

- Resource/type detection is **name-based** (no type resolution) — false positives are expected and `--judge` exists to filter them.
- Deterministic autofix covers only `resource-leak`'s provably-safe subset (single never-closed resource directly in a block, wrapped in try-with-resources). Everything else is a `= help:` suggestion or AI-fixed.
- Formatting reflow is delegated to `google-java-format` (system binary, not the pre-commit bundled hook which needs JDK 21+).

# RuleSmith

NL coding rules -> tested, AST-backed deterministic checks. Neuro-symbolic linter:
deterministic primitives (CFG, dominance) compute the expensive-to-be-wrong facts;
Claude adjudicates only the fuzzy residual. Every finding cites its evidence.

Design docs + 184-rule catalog: see the agentathon vault notes.

## Decisions (locked)
- Name: RuleSmith
- Flagship rule: resource-leak
- Engine: raw tree-sitter (py bindings) -- need full AST for CFG
- Spec format: python DSL (rule = function -> findings)
- MVP language: Java
- LLM: Claude API, claude-opus-4-8 (codegen + judge), wired later

## Layout
```
rulesmith/
  parse.py   # Phase 0: parse + ast query/find, spans, node text
  cfg.py     # Phase 1: intraprocedural CFG + dominance / post-dominance
rules/       # rule specs (python) -- next
fixtures/    # pos/neg test cases per rule
```

## Dev
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m rulesmith.cfg   # primitive self-check
```

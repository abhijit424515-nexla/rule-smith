"""Phase 4: authoring loop. English rule -> codegen -> verify -> install.

Compiles a natural-language rule into a python rule module + pos/neg
fixtures via `claude -p`, then runs the fixtures as a gate. Installs only
on green; on failure feeds the errors back and retries once.
"""

import importlib.util
import os

from .llm import complete, extract_json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_DIR = os.path.join(ROOT, "rules")
FIX_DIR = os.path.join(ROOT, "fixtures")

API = """\
RuleSmith primitive API (import these; do not reimplement parsing):

  from rulesmith.parse import parse, find, span, node_text, walk
  from rulesmith.cfg import build_method, dominators, postdominators, dominates, postdominates
  from rulesmith.dataflow import escapes, defs_uses

  parse(src) -> (tree, src_bytes)
  find(node, *types) -> list of descendant nodes of those tree-sitter types
  node_text(node, src_bytes) -> str ; span(node) -> (line,col,endline,endcol) 1-based
  build_method(method_ts, src_bytes) -> CFG ; nodes wrap tree-sitter statements
  dominators(cfg)/postdominators(cfg) -> {node_id: set(dominator_ids)}
  dominates(dom,a_id,b_id) / postdominates(pdom,a_id,b_id) -> bool
  escapes(method_ts, varname) -> bool ; defs_uses(method_ts, varname) -> (defs,uses)

A rule MODULE must define:
  RULE = "kebab-case-id"
  def analyze_source(src, file="<src>") -> list[finding]
A finding is a dict: {"rule":RULE,"file":file,"line":int,"col":int,
  "message":str,"note":str(evidence),"help":str}
Iterate methods with: find(tree.root_node,"method_declaration","constructor_declaration")
Common tree-sitter-java node types: method_invocation (fields object,name,arguments),
  binary_expression (fields left,operator,right), local_variable_declaration
  (fields type, then variable_declarator with fields name,value), if_statement
  (fields condition,consequence,alternative), identifier, string_literal.
"""

PROMPT = """You compile a natural-language coding rule into a RuleSmith python rule \
module plus test fixtures. Output ONLY a JSON object, no prose.

{api}

The rule to implement: "{rule}"

Return JSON with this exact shape:
{{
  "rule_id": "kebab-case",
  "module": "<full python source of the rule module>",
  "fixtures": [
    {{"file": "violation.java", "code": "<java that VIOLATES the rule>", "expect": 1}},
    {{"file": "clean.java", "code": "<java that does NOT violate>", "expect": 0}}
  ]
}}
Provide at least 2 violation fixtures and 2 clean fixtures. Keep the module \
deterministic and small. Use the primitive API; never use regex on raw source for \
structure. expect = number of findings analyze_source should return for that file. Each fixture's java MUST be a COMPLETE compilation unit (a full class with the snippet wrapped inside a method/class), never a bare method or statement snippet, so external formatters can parse it."""


def _load(path):
    spec = importlib.util.spec_from_file_location(
        "genrule_" + os.path.basename(path), path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _verify(module_code, fixtures, tmp):
    """Returns (ok, report_lines). Writes module to tmp, runs fixtures."""
    with open(tmp, "w") as f:
        f.write(module_code)
    rep = []
    try:
        mod = _load(tmp)
    except Exception as e:
        return False, [f"module import error: {e}"]
    if not hasattr(mod, "analyze_source") or not hasattr(mod, "RULE"):
        return False, ["module missing RULE or analyze_source"]
    ok = True
    for fx in fixtures:
        try:
            got = len(mod.analyze_source(fx["code"], fx["file"]))
        except Exception as e:
            ok = False
            rep.append(f"  [ERR ] {fx['file']}: raised {e}")
            continue
        exp = fx["expect"]
        if got != exp:
            ok = False
            rep.append(f"  [FAIL] {fx['file']}: got {got}, expected {exp}")
        else:
            rep.append(f"  [ok  ] {fx['file']}: {got}")
    return ok, rep


def add_rule(english, max_attempts=2, model=None):
    import tempfile

    _fd, tmp = tempfile.mkstemp(prefix="rulesmith_gen_", suffix=".py")
    os.close(_fd)
    feedback = ""
    for attempt in range(1, max_attempts + 1):
        prompt = PROMPT.format(api=API, rule=english)
        if feedback:
            prompt += (
                "\n\nYour previous attempt FAILED its fixtures:\n"
                + feedback
                + "\nFix the module so every fixture matches its expected count. Output JSON only."
            )
        print(f"[attempt {attempt}] asking claude -p to compile the rule...")
        reply = complete(prompt, model=model)
        try:
            spec = extract_json(reply)
        except Exception as e:
            feedback = f"could not parse your JSON: {e}"
            continue
        rid = spec["rule_id"]
        ok, rep = _verify(spec["module"], spec["fixtures"], tmp)
        print("\n".join(rep))
        if ok:
            # install
            dest = os.path.join(RULES_DIR, rid.replace("-", "_") + ".py")
            header = f"# rule: {english}\n# (authored by RuleSmith from the description above)\n\n"
            with open(dest, "w") as f:
                f.write(header + spec["module"])
            fxd = os.path.join(FIX_DIR, rid.replace("-", "_"))
            os.makedirs(fxd, exist_ok=True)
            for fx in spec["fixtures"]:
                with open(os.path.join(fxd, fx["file"]), "w") as f:
                    f.write(fx["code"])
            print(
                f"\ninstalled rule '{rid}' -> {os.path.relpath(dest, ROOT)} "
                f"({len(spec['fixtures'])} fixtures, all green)"
            )
            return rid
        feedback = "\n".join(rep)
        print(f"[attempt {attempt}] fixtures failed; retrying with feedback\n")
    print(f"\nfailed to author a passing rule after {max_attempts} attempts.")
    return None

---
marp: true
theme: default
paginate: true
style: |
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Raleway:wght@100;200;300&display=swap');
  section { background: #000; color: #fff; font-family: 'Raleway', sans-serif; font-weight: 200; padding: 52px 68px; line-height: 1.5; font-size: 21px; }
  h1 { font-family: 'Outfit'; font-weight: 800; font-size: 2.7em; color: #fff; letter-spacing: -0.02em; line-height: 1.04; margin: 0 0 6px; }
  h2 { font-family: 'Raleway'; font-weight: 100; font-size: 1.2em; color: #888; margin: 0 0 18px; }
  h3 { font-family: 'Outfit'; font-weight: 600; font-size: 0.62em; color: #555; text-transform: uppercase; letter-spacing: 0.22em; margin: 0 0 6px; }
  strong { color: #ff6b1a; font-weight: 300; }
  em { color: #bbb; font-style: italic; }
  code { font-family: 'Courier New', monospace; background: #0c0c0c; color: #ff8c4a; padding: 1px 6px; border-radius: 4px; font-size: 0.85em; }
  a { color: #ff6b1a; }
  ul { margin-top: 6px; } li { margin: 5px 0; color: #aaa; }
  section::after { font-family: 'Outfit'; font-size: 0.5em; color: #222; }
  section.lead { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
  .terminal { background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 12px; overflow: hidden; font-family: 'Courier New', monospace; font-size: 0.72em; margin-top: 14px; }
  .tbar { background: #111; padding: 8px 14px; display: flex; gap: 6px; align-items: center; }
  .dot { width: 10px; height: 10px; border-radius: 50%; }
  .tbody { padding: 16px 20px; line-height: 1.7; }
  .prompt { color: #ff6b1a; }
  .out { color: #777; }
  .ok { color: #22c55e; }
  .warn { color: #f5a623; }
  .bad { color: #ef4444; }
  .split { display: flex; gap: 18px; margin-top: 16px; }
  .pane { flex: 1; background: #080808; border: 1px solid #141414; border-radius: 10px; padding: 16px 18px; }
  .pane.before { border-top: 2px solid #ef4444; }
  .pane.after { border-top: 2px solid #22c55e; }
  .card { background: #080808; border: 1px solid #141414; border-radius: 10px; padding: 14px 18px; }
  .big { font-family: 'Outfit'; font-weight: 800; font-size: 2em; color: #fff; }
  .tag { font-family: 'Outfit'; font-weight: 600; font-size: 0.6em; letter-spacing: 0.1em; text-transform: uppercase; padding: 3px 10px; border-radius: 4px; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.8em; }
  th { text-align: left; color: #555; font-family: 'Outfit'; font-weight: 600; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.1em; border-bottom: 1px solid #1a1a1a; padding: 8px 10px; }
  table, tr, th, td { background: transparent !important; }
  td { color: #aaa; padding: 9px 10px; border-bottom: 1px solid #0e0e0e; }
---

<!-- _class: lead -->

### Deterministic linting, authored in English

# RuleSmith

## A rulebook a machine *runs* — not one an LLM *reads*

<!--
~7 min demo. Setup off-screen:
  cd ~/workspace/experiments/rule-smith && source .venv/bin/activate
  BC=~/Desktop/clones/backend-connectors
  TEN=resource-leak,optional-get-without-ispresent,null-deref-needs-dominating-guard,unchecked-downcast,field-read-before-assign,non-atomic-shared-update,guarded-by-lock-held,no-string-concat-in-loop,no-superfluous-else,constructor-definite-assignment
Record a fallback video of the `add` beat (calls claude -p, network-dependent).
-->

---

### The trap everyone falls into

# "Just put the rules in CLAUDE.md"

Small team, no time to police architecture. The reflex: write the rules into a
CLAUDE.md and let the AI handle it.

A CLAUDE.md rule is **prose read by an LLM that pattern-matches text**. It has no
control-flow graph. So it cannot answer:

- *Is `close()` on **every** path, including the early return?*
- *Does the null-check **dominate** this dereference?*

Same tokens, different flow — bug here, fine there. **You cannot vibe that out of
a sentence.**

<!--
Beat 0, 45s, no terminal. This is the whole thesis. Land it slowly. The audience
has all written a CLAUDE.md rulebook; name that reflex, then show why it leaks.
-->

---

### Beat 1 — the core argument

# Same code. Different flow. Opposite verdict.

`examples/java/PaymentGateway.java` — ten methods that each look ordinary
line-by-line.

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules $TEN examples/java<br/>
<span class="warn">warning[resource-leak]</span>: `in` is never closed<br/>
<span class="out">   = note: close() is on no path (post-dominance)</span><br/>
<span class="warn">warning[optional-get-without-ispresent]</span>: `acct.get()` not guarded<br/>
<span class="out">...</span><br/>
<span class="bad">12 findings</span><br/><br/>
<span class="prompt">$</span> rulesmith lint --rules $TEN examples/java-fixed<br/>
<span class="ok">0 findings</span>
</div>
</div>

The verdict flipped on the **flow**, not the syntax.

<!--
Beat 1, 110s, the money slide. Read two methods aloud first: the leak with the
early return, the Optional.get() after a branch. "Would you catch these in review?
Would a prose rule?" Then run both commands. Punchline: a CLAUDE.md rule sees
near-identical code in both files and can't tell them apart.
-->

---

### What a prose rule structurally cannot see

# Ten flow-sensitive checks

<div style="display:flex; gap:18px;">
<div style="flex:1;">

- **resource-leak** — close() on every path?
- **optional-get** — get() dominated by isPresent()?
- **null-deref** — guard misses one path
- **unchecked-downcast** — cast without instanceof
- **field-read-before-assign** — read before set

</div>
<div style="flex:1;">

- **non-atomic-shared-update** — read-mod-write
- **guarded-by-lock-held** — field w/o its lock
- **no-string-concat-in-loop** — O(n²) build
- **no-superfluous-else** — else after return
- **constructor-definite-assignment**

</div>
</div>

Each needs a **control-flow graph + dominance** — exactly what an LLM reading a
sentence does not build.

<!--
Beat 1 continued. Optional slide — skip if short on time. The point: these aren't
style nits, they're correctness bugs that are invisible to text matching.
-->

---

### Beat 2 — not a toy

# A real leak, in shipped code

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules resource-leak \<br/>
<span class="out">    $BC/.../onedrive/OneDriveConnectorService.java</span><br/><br/>
<span class="warn">warning[resource-leak]</span>: `fileInput` (FileInputStream) is never closed<br/>
<span class="out">  --> OneDriveConnectorService.java:516</span><br/>
<span class="out">   = note: close() is on no path; resource does not escape</span><br/>
<span class="out">   = help: use try-with-resources</span>
</div>
</div>

The `= note:` is **deterministic evidence** — a graph fact, reproducible every
run. Not a vibe.

<!--
Beat 2, 75s. Point at the finding. This is real production code in backend-
connectors. Stress: every finding cites WHY, and the why is a CFG fact, not a
language-model opinion.
-->

---

### Beat 3 — the catalog writes itself

# Describe a rule in English

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith add "a switch over an enum must have a default case"<br/>
<span class="out">[attempt 1] compiling rule via claude -p...</span><br/>
<span class="ok">[ok]</span> violation.java: 1 &nbsp; <span class="ok">[ok]</span> clean.java: 0<br/>
<span class="ok">installed rule 'enum-switch-default' (4 fixtures, all green)</span>
</div>
</div>

The LLM writes the rule — but a **deterministic fixture gate** decides if it
ships. That gate is exactly what a CLAUDE.md rule never gets.

<!--
Beat 3, 90s. This is why you can TRUST an AI-authored rule: it must pass pos/neg
fixtures before install. Fallback: play the recording if the network stalls.
113 rules already shipped this way.
-->

---

### Why you can trust an AI-written rule

# AI builds the checks. Code runs them.

<table>
<tr><th>Action</th><th>Needs Claude?</th><th>Why</th></tr>
<tr><td>lint / list / --fix / CI gate</td><td><span class="ok">No</span></td><td>pure CFG + AST, deterministic, offline</td></tr>
<tr><td>add "&lt;english&gt;"</td><td><span class="warn">Once</span></td><td>codegen, then gated by fixtures</td></tr>
<tr><td>lint --judge</td><td><span class="warn">Cached</span></td><td>adjudicate, then cached → AI-free</td></tr>
</table>

The everyday workflow is **100% deterministic and runs forever with no API key**.
Claude is touched only to *author* a rule and (optionally) to *adjudicate* —
both gated, both cached.

<!--
This slide preempts the obvious objection: "isn't this just AI linting?" No —
the runtime is deterministic code. AI is the author and the occasional judge,
never the everyday engine.
-->

---

### Beat 4 — it polices itself

# Filters its own false positives

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules resource-leak --judge $BC/.../IcebergSourceTask.java<br/><br/>
<span class="out">1 finding filtered as false positive by the judge:</span><br/>
<span class="out">  filtered[resource-leak] IcebergSourceTask.java:101: `reader` never closed</span><br/>
<span class="ok">   = judge: not a real issue — OffsetStorageReader is framework-managed;</span><br/>
<span class="ok">     Kafka Connect handles the lifecycle</span>
</div>
</div>

Primitives are conservative on purpose; **Claude adjudicates the residual, and
the verdict is cached** so it's reproducible.

<!--
Beat 4, 75s. Name-based heuristic flags OffsetStorageReader; the judge knows it's
framework-managed and filters it. Cached by (rule, snippet) so the same code
always gets the same verdict — AI-in-the-loop without losing reproducibility.
-->

---

### Beat 5 — and it fixes them

# Safe autofix, the rest suggested

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --fix --dry-run --rules resource-leak \<br/>
<span class="out">    $BC/.../OneDriveConnectorService.java</span><br/><br/>
<span class="out">would fix: 2 resource(s) wrapped in try-with-resources</span><br/>
<span class="ok">2 auto-fixed</span>, <span class="warn">1 needs manual handling (suggest-only)</span>
</div>
</div>

Only the **provably-safe subset** auto-fixes. Everything else stays a suggestion,
with rustc-style help + doc link.

<!--
Beat 5, 45s. Same file as Beat 2. The split (2 auto, 1 suggest) shows the tool is
conservative about rewriting code — it won't corrupt anything it isn't sure of.
-->

---

### Beat 6 — does it work on real code?

# Five unmodified production files

<div style="display:flex; gap:14px; margin-top:10px;">
<div class="card" style="flex:1; text-align:center;"><div class="big">5</div><div style="color:#666; font-size:0.7em;">FILES</div></div>
<div class="card" style="flex:1; text-align:center;"><div class="big">236</div><div style="color:#666; font-size:0.7em;">FINDINGS</div></div>
<div class="card" style="flex:1; text-align:center;"><div class="big">13-15</div><div style="color:#666; font-size:0.7em;">RULES / FILE</div></div>
<div class="card" style="flex:1; text-align:center;"><div class="big">0</div><div style="color:#666; font-size:0.7em;">PARSE ERRORS</div></div>
</div>

Vendored into `examples/real-world/` so the findings reproduce without the repo:
<code>rulesmith lint examples/real-world</code>

<!--
Beat 6, 90s. Whole-repo proof: 1242 files, 0 parse errors. These five are
representative. Next five slides: one per file. Use --rules <id> to isolate one
check per slide if you want to drill in.
-->

---

### Real file · vectordb probe

# PineconeHelper.java

<span class="tag" style="background:#ef444412; color:#ef4444; border:1px solid #ef444422;">28 findings · 14 rules</span>

<div class="terminal" style="font-size:0.5em">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules no-generic-catch,broad-exception-catch examples/real-world/PineconeHelper.java<br/>
<span class="warn">warning[broad-exception-catch]</span>: Catching broad type &#x27;Exception&#x27; traps JVM errors and unrelated bugs.<br/>
<span class="out">  --&gt; examples/real-world/PineconeHelper.java:70:14</span><br/>
<span class="out">   = note: catch (Exception ...)</span><br/>
<span class="out">   = help: Catch the narrowest applicable exception type instead.</span><br/>
<span class="out">   = see:  https://rules.smith.dev/broad-exception-catch</span><br/>
&nbsp;<br/>
<span class="warn">warning[no-generic-catch]</span>: catch block catches generic &#x27;Exception&#x27;<br/>
<span class="out">  --&gt; examples/real-world/PineconeHelper.java:70:14</span><br/>
<span class="out">   = note: catch (Exception e) {</span><br/>
<span class="out">   = help: Catch a specific exception subclass instead of &#x27;Exception&#x27;.</span><br/>
<span class="out">   = see:  https://rules.smith.dev/no-generic-catch</span><br/>
&nbsp;
</div>
</div>

A CLAUDE.md "handle errors properly" rule is unenforceable prose; this flags the **exact site**.

<!-- Beat 6, slide 1 of 5. Error-handling debt you can describe but not enforce in prose. -->

---

### Real file · parsers / writer

# ExcelFileWriter.java

<span class="tag" style="background:#ef444412; color:#ef4444; border:1px solid #ef444422;">62 findings · 13 rules</span>

<div class="terminal" style="font-size:0.5em">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules resource-leak examples/real-world/ExcelFileWriter.java<br/>
<span class="warn">warning[resource-leak]</span>: `customHeader` (StringWriter) is never closed<br/>
<span class="out">  --&gt; examples/real-world/ExcelFileWriter.java:126:11</span><br/>
<span class="out">   = note: no close() call found and the resource does not escape the method</span><br/>
<span class="out">   = help: close it in a finally block, or use try-with-resources: try (StringWriter customHeader = ...) { ... }</span><br/>
<span class="out">   = see:  https://rules.smith.dev/resource-leak</span><br/>
&nbsp;
</div>
</div>

Proven via **post-dominance** — close() is on no path — not guessed from the name.

<!-- Beat 6, slide 2 of 5. The leak is proven by graph reachability, not a name heuristic. -->

---

### Real file · jdbc source

# TimestampModeProcessor.java

<span class="tag" style="background:#f5a62312; color:#f5a623; border:1px solid #f5a62322;">18 findings · 14 rules</span>

<div class="terminal" style="font-size:0.5em">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules null-deref-needs-dominating-guard examples/real-world/TimestampModeProcessor.java<br/>
<span class="warn">warning[null-deref-needs-dominating-guard]</span>: &#x27;result&#x27; may be null here and is dereferenced without a dominating null guard<br/>
<span class="out">  --&gt; examples/real-world/TimestampModeProcessor.java:165:30</span><br/>
<span class="out">   = note: result.getFrom()</span><br/>
<span class="out">   = help: Add a check like `if (result != null)` that dominates this access, or an early `if (result == null) return;` guard before it</span><br/>
<span class="out">   = see:  https://rules.smith.dev/null-deref-needs-dominating-guard</span><br/>
&nbsp;<br/>
<span class="warn">warning[null-deref-needs-dominating-guard]</span>: &#x27;result&#x27; may be null here and is dereferenced without a dominating null guard<br/>
<span class="out">  --&gt; examples/real-world/TimestampModeProcessor.java:165:49</span><br/>
<span class="out">   = note: result.getTo()</span><br/>
<span class="out">   = help: Add a check like `if (result != null)` that dominates this access, or an early `if (result == null) return;` guard before it</span><br/>
<span class="out">   = see:  https://rules.smith.dev/null-deref-needs-dominating-guard</span><br/>
&nbsp;
</div>
</div>

The canonical *"looks fine line-by-line, NPE on one path"* bug. Only a CFG sees it.

<!-- Beat 6, slide 3 of 5. The flagship flow-sensitivity argument, now on real code. -->

---

### Real file · xml parser

# XmlUtils.java

<span class="tag" style="background:#f5a62312; color:#f5a623; border:1px solid #f5a62322;">48 findings · 13 rules</span>

<div class="terminal" style="font-size:0.5em">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules unchecked-downcast examples/real-world/XmlUtils.java<br/>
<span class="warn">warning[unchecked-downcast]</span>: downcast `(Map&lt;String, Object&gt;) el` is not guarded by an instanceof check<br/>
<span class="out">  --&gt; examples/real-world/XmlUtils.java:119:41</span><br/>
<span class="out">   = note: no `el instanceof` test dominates this cast; throws ClassCastException when the runtime type differs</span><br/>
<span class="out">   = help: guard with if (el instanceof Map&lt;String, Object&gt;) before casting</span><br/>
<span class="out">   = see:  https://rules.smith.dev/unchecked-downcast</span><br/>
&nbsp;
</div>
</div>

Dominance decides whether the guard actually **covers** the cast.

<!-- Beat 6, slide 4 of 5. Same dominance primitive, different bug class. -->

---

### Real file · script-runner

# SQLScriptExecutor.java

<span class="tag" style="background:#ef444412; color:#ef4444; border:1px solid #ef444422;">80 findings · 15 rules</span>

<div class="terminal" style="font-size:0.5em">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules broad-exception-catch examples/real-world/SQLScriptExecutor.java<br/>
<span class="warn">warning[broad-exception-catch]</span>: Catching broad type &#x27;Exception&#x27; traps JVM errors and unrelated bugs.<br/>
<span class="out">  --&gt; examples/real-world/SQLScriptExecutor.java:64:14</span><br/>
<span class="out">   = note: catch (Exception ...)</span><br/>
<span class="out">   = help: Catch the narrowest applicable exception type instead.</span><br/>
<span class="out">   = see:  https://rules.smith.dev/broad-exception-catch</span><br/>
&nbsp;<br/>
<span class="warn">warning[broad-exception-catch]</span>: Catching broad type &#x27;Exception&#x27; traps JVM errors and unrelated bugs.<br/>
<span class="out">  --&gt; examples/real-world/SQLScriptExecutor.java:110:14</span><br/>
<span class="out">   = note: catch (Exception ...)</span><br/>
<span class="out">   = help: Catch the narrowest applicable exception type instead.</span><br/>
<span class="out">   = see:  https://rules.smith.dev/broad-exception-catch</span><br/>
&nbsp;<br/>
<span class="warn">warning[broad-exception-catch]</span>: Catching broad type &#x27;Throwable&#x27; traps JVM errors and unrelated bugs.<br/>
<span class="out">  --&gt; examples/real-world/SQLScriptExecutor.java:126:14</span><br/>
<span class="out">   = note: catch (Throwable ...)</span><br/>
<span class="out">   = help: Catch the narrowest applicable exception type instead.</span><br/>
<span class="out">   = see:  https://rules.smith.dev/broad-exception-catch</span><br/>
&nbsp;<br/>
<span class="out">... (3 more)</span>
</div>
</div>

Systemic error-handling debt a rulebook *describes* but cannot **count**.

<!-- Beat 6, slide 5 of 5. Scale: a rulebook says "don't swallow exceptions"; RuleSmith hands you the 15 sites. -->

---

<!-- _class: lead -->

### The whole thing in one line

# CLAUDE.md is read.
# RuleSmith is run.

<div style="display:flex; gap:18px; margin-top:24px;">
<div class="card"><strong>113 rules</strong> implemented</div>
<div class="card"><strong>184-rule</strong> catalog mined</div>
<div class="card"><strong>0</strong> API keys to run</div>
</div>

<div style="color:#555; font-size:0.7em; margin-top:22px;">
tree-sitter + CFG/dominance + claude -p · sources: Checker Framework, Effective Java, NASA Power of Ten, OWASP, FP literature
</div>

<!--
Close, 30s. The catalog is mined from real authority (not invented). The runtime
is deterministic. The authoring is AI. One CLI, no key for everyday use.
Cheat sheet to point at:
- 10 flow-sensitive rules: examples/java/PaymentGateway.java (12) vs java-fixed (0)
- Real leak: OneDriveConnectorService.java:516 fileInput (FileInputStream)
- Filtered FP: IcebergSourceTask.java reader (OffsetStorageReader)
- Real files: rulesmith lint examples/real-world (5 files, 13-15 rules each)
-->

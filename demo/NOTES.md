---
marp: true
theme: default
paginate: true
style: |
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Raleway:wght@100;200;300&display=swap');
  section { background: #000; color: #fff; font-family: 'Raleway', sans-serif; font-weight: 200; padding: 52px 68px; line-height: 1.5; font-size: 21px; }
  h1 { font-family: 'Outfit'; font-weight: 800; font-size: 2.6em; color: #fff; letter-spacing: -0.02em; line-height: 1.04; margin: 0 0 6px; }
  h2 { font-family: 'Raleway'; font-weight: 100; font-size: 1.2em; color: #888; margin: 0 0 18px; }
  h3 { font-family: 'Outfit'; font-weight: 600; font-size: 0.62em; color: #555; text-transform: uppercase; letter-spacing: 0.22em; margin: 0 0 6px; }
  strong { color: #ff6b1a; font-weight: 300; }
  em { color: #bbb; font-style: italic; }
  code { font-family: 'Courier New', monospace; background: #0c0c0c; color: #ff8c4a; padding: 1px 6px; border-radius: 4px; font-size: 0.85em; }
  ul { margin-top: 6px; } li { margin: 5px 0; color: #aaa; }
  section::after { font-family: 'Outfit'; font-size: 0.5em; color: #222; }
  section.lead { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }
  .terminal { background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 12px; overflow: hidden; font-family: 'Courier New', monospace; font-size: 0.62em; margin-top: 14px; }
  .tbar { background: #111; padding: 8px 14px; display: flex; gap: 6px; align-items: center; }
  .dot { width: 10px; height: 10px; border-radius: 50%; }
  .tbody { padding: 16px 20px; line-height: 1.7; }
  .prompt { color: #ff6b1a; } .out { color: #777; } .ok { color: #22c55e; } .warn { color: #f5a623; } .bad { color: #ef4444; }
  .card { background: #080808; border: 1px solid #141414; border-radius: 10px; padding: 14px 18px; }
  .big { font-family: 'Outfit'; font-weight: 800; font-size: 2em; color: #fff; }
  .tag { font-family: 'Outfit'; font-weight: 600; font-size: 0.6em; letter-spacing: 0.1em; text-transform: uppercase; padding: 3px 10px; border-radius: 4px; }
  table, tr, th, td { background: transparent !important; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.8em; }
  th { text-align: left; color: #555; font-family: 'Outfit'; font-weight: 600; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.1em; border-bottom: 1px solid #1a1a1a; padding: 8px 10px; }
  td { color: #aaa; padding: 9px 10px; border-bottom: 1px solid #0e0e0e; }
---

<!-- _class: lead -->

### Deterministic linting, authored in English

# RuleSmith

## A rulebook a machine *runs* — not one an LLM *reads*

<!--
~7 min. Setup off-screen:
  cd ~/workspace/experiments/rule-smith && source .venv/bin/activate
  BC=~/Desktop/clones/backend-connectors
  FIVE=builder-terminal-before-setters,pure-method-no-side-effects,guarded-by-lock-held,blocking-call-while-holding-lock,lambda-captures-mutable-state
Record a fallback video of the `add` beat (calls claude -p).
-->

---

### The trap everyone falls into

# "Just put the rules in CLAUDE.md"

A CLAUDE.md rule is **prose pattern-matched by an LLM**. It has no control-flow
graph, no call graph, no notion of lock state or call ordering. So it cannot
answer the questions that catch the *expensive* bugs:

- *Is this `build()` called **before** a required setter?* (typestate)
- *Does a thread read-modify-write a shared field **without the lock**?*
- *Is this `@Pure` method actually pure?*

These aren't style nits. They're the bugs **SonarQube and PMD don't catch
either** — and you certainly can't vibe them out of a sentence.

<!-- Beat 0, 45s. Set up that the interesting rules are the ones standard tools miss. -->

---

### Beat 1 — the core argument

# Same code. Different flow. Opposite verdict.

`examples/java/PaymentGateway.java` — five defects no syntax rule can see.

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules $FIVE examples/java<br/>
<span class="warn">warning[builder-terminal-before-setters]</span>: 'b' finalized by build() before setter total()<br/>
<span class="warn">warning[guarded-by-lock-held]</span>: @GuardedBy field 'balance' read without the lock<br/>
<span class="warn">warning[blocking-call-while-holding-lock]</span>: fut.get() blocks while holding a lock<br/>
<span class="warn">warning[pure-method-no-side-effects]</span>: @Pure method calls a mutating method<br/>
<span class="warn">warning[lambda-captures-mutable-state]</span>: lambda mutates captured array 'acc'<br/>
<span class="bad">5 findings</span><br/><br/>
<span class="prompt">$</span> rulesmith lint --rules $FIVE examples/java-fixed<br/>
<span class="ok">0 findings</span>
</div>
</div>

The verdict flipped on the **flow**, not the syntax.

<!-- Beat 1, 110s. The money slide. Typestate, lock-dominance, deadlock, purity, closure capture -- all in one screen. -->

---

### What standard linters structurally cannot see

# The differentiated ten

<div style="display:flex; gap:18px;">
<div style="flex:1;">

- **resource-leak** — close() on every path (post-dom)
- **builder-terminal-before-setters** — *typestate*: call ordering
- **atomic-get-set-race** — get()→set() defeats atomicity
- **guarded-by-lock-held** — @GuardedBy without the lock
- **blocking-call-while-holding-lock** — deadlock risk

</div>
<div style="flex:1;">

- **command-query-separation** — returns *and* mutates
- **pure-method-no-side-effects** — purity via call graph
- **local-throw-catch-control-flow** — exception as goto
- **tell-dont-ask** — get-then-mutate from outside
- **lambda-captures-mutable-state** — closure capture

</div>
</div>

Typestate, lock dominance, purity, atomicity — **not** the textbook null-check
every linter ships. These need a real CFG, call graph, and dataflow.

<!-- Beat 1 continued. This is the slide that answers "isn't this just SonarQube?". No -- these are the ones it misses. -->

---

### Beat 2 — a real catch, not a toy

# A concurrency race in shipped code

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules atomic-get-set-race .../pdf/strategy/DefaultStrategy.java<br/><br/>
<span class="warn">warning[atomic-get-set-race]</span>: Non-atomic get-then-set on Atomic 'textBB' loses concurrent updates.<br/>
<span class="out">  --> DefaultStrategy.java:69</span><br/>
<span class="out">   = note: value passed to textBB.set(...) is computed from textBB.get();</span><br/>
<span class="out">     another thread can update between the get and the set.</span><br/>
<span class="out">   = help: use textBB.updateAndGet(...) or compareAndSet(...)</span>
</div>
</div>

`textBB.set(textBB.get() == null ? ... )` — a textbook lost-update race, in
production, found deterministically. **No string rule finds this.**

<!-- Beat 2, 75s. The star finding. Real backend-connectors code. Read the textBB line aloud. -->

---

### Why you can trust an AI-written rule

# AI builds the checks. Code runs them.

<table>
<tr><th>Action</th><th>Needs Claude?</th><th>Why</th></tr>
<tr><td>lint · list · --fix · CI gate</td><td><span class="ok">No</span></td><td>pure CFG + AST, deterministic, offline</td></tr>
<tr><td>add "&lt;english&gt;"</td><td><span class="warn">Once</span></td><td>codegen, then gated by fixtures</td></tr>
<tr><td>lint --judge</td><td><span class="warn">Cached</span></td><td>adjudicate, then cached → AI-free</td></tr>
</table>

The everyday workflow runs forever with **no API key**. Claude only *authors* a
rule (gated by tests) and optionally *adjudicates* a borderline finding (cached).

<!-- Preempts "isn't this just AI linting?". The runtime is deterministic code. -->

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

The LLM writes the rule — a **deterministic fixture gate** decides if it ships.
That gate is exactly what a CLAUDE.md rule never gets. **114 rules** shipped this
way.

<!-- Beat 3, 90s. Trust = the fixture gate. Fallback: play recording. -->

---

### Beat 4 — it polices itself

# Filters its own false positives

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules resource-leak --judge .../IcebergSourceTask.java<br/><br/>
<span class="out">1 finding filtered as false positive by the judge:</span><br/>
<span class="out">  filtered[resource-leak] IcebergSourceTask.java:101: `reader` never closed</span><br/>
<span class="ok">   = judge: OffsetStorageReader is framework-managed; Kafka Connect</span><br/>
<span class="ok">     handles the lifecycle</span>
</div>
</div>

Primitives are conservative on purpose; **Claude adjudicates the residual, and the
verdict is cached** by `(rule, snippet)` so it's reproducible.

<!-- Beat 4, 75s. AI-in-the-loop without losing reproducibility. -->

---

### Beat 5 — and it fixes them

# Safe autofix, the rest suggested

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --fix --dry-run --rules resource-leak .../OneDriveConnectorService.java<br/><br/>
<span class="out">would fix: 2 resource(s) wrapped in try-with-resources</span><br/>
<span class="ok">2 auto-fixed</span>, <span class="warn">1 needs manual handling (suggest-only)</span>
</div>
</div>

Only the **provably-safe subset** auto-fixes — a pure deterministic codemod, no AI.
Everything else stays a rustc-style suggestion with help + doc link.

<!-- Beat 5, 45s. The tool never AI-rewrites code; it won't touch what it can't prove safe. -->

---

### Beat 6 — does it work on real code?

# Differentiated rules, real production files

<div style="display:flex; gap:14px; margin-top:10px;">
<div class="card" style="flex:1; text-align:center;"><div class="big">114</div><div style="color:#666; font-size:0.7em;">RULES</div></div>
<div class="card" style="flex:1; text-align:center;"><div class="big">1242</div><div style="color:#666; font-size:0.7em;">FILES SCANNED</div></div>
<div class="card" style="flex:1; text-align:center;"><div class="big">0</div><div style="color:#666; font-size:0.7em;">PARSE ERRORS</div></div>
</div>

The next slides are **real findings** from backend-connectors — the differentiated
checks SonarQube doesn't run, firing on shipped code.

<!-- Beat 6, 90s. Five real findings, one per slide. The atomic race already shown is the headliner. -->

---

### Real catch · concurrency

# atomic-get-set-race

<span class="tag" style="background:#ef444412; color:#ef4444; border:1px solid #ef444422;">parsers · DefaultStrategy.java:69</span>

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules atomic-get-set-race examples/real-world/... <br/>
<span class="warn">warning[atomic-get-set-race]</span>: Non-atomic get-then-set on Atomic 'textBB' loses concurrent updates.<br/>
<span class="out">  --> DefaultStrategy.java:69</span><br/>
<span class="out">   = note: value passed to set() is computed from get(); a thread can update between</span>
</div>
</div>

A lost-update race a code reviewer would miss and a prose rule cannot express.

<!-- Real file 1/5. The headliner. -->

---

### Real catch · design

# tell-dont-ask

<span class="tag" style="background:#f5a62312; color:#f5a623; border:1px solid #f5a62322;">ftp-probe · FtpClientImpl.java:337</span>

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules tell-dont-ask .../FtpClientImpl.java<br/>
<span class="warn">warning[tell-dont-ask]</span>: decide on nextReportTime.get() then nextReportTime.set() outside the object.<br/>
<span class="out">  --> FtpClientImpl.java:337</span><br/>
<span class="out">   = note: if (currentTime > nextReportTime.get()) { ... nextReportTime.set(...) }</span>
</div>
</div>

Get-state-then-mutate from outside — the decision belongs *inside* the object.

<!-- Real file 2/5. Design smell, real code. -->

---

### Real catch · exceptions

# local-throw-catch-control-flow

<span class="tag" style="background:#f5a62312; color:#f5a623; border:1px solid #f5a62322;">ftp-probe · FtpConnectorService.java:415</span>

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules local-throw-catch-control-flow .../FtpConnectorService.java<br/>
<span class="warn">warning[local-throw-catch-control-flow]</span>: 'IllegalStateException' thrown and caught locally in the same method,<br/>
<span class="warn">  steering control flow instead of signaling a fault.</span><br/>
<span class="out">  --> FtpConnectorService.java:415</span>
</div>
</div>

Exception used as a goto — `throw` post-dominated by its own `catch`.

<!-- Real file 3/5. CFG post-dominance over exception edges. -->

---

### Real catch · design

# command-query-separation

<span class="tag" style="background:#f5a62312; color:#f5a623; border:1px solid #f5a62322;">ftp-probe · FtpClientImpl.java:72</span>

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules command-query-separation .../FtpClientImpl.java<br/>
<span class="warn">warning[command-query-separation]</span>: Method 'create' returns a value and also mutates observable state.<br/>
<span class="out">  --> FtpClientImpl.java:72</span><br/>
<span class="out">   = help: split into a void command and a side-effect-free query</span>
</div>
</div>

A query that secretly mutates — the bug class CQS exists to prevent.

<!-- Real file 4/5. -->

---

### Real catch · resource lifecycle

# resource-leak

<span class="tag" style="background:#ef444412; color:#ef4444; border:1px solid #ef444422;">one-drive · OneDriveConnectorService.java:392</span>

<div class="terminal">
<div class="tbar"><div class="dot" style="background:#ff5f56"></div><div class="dot" style="background:#ffbd2e"></div><div class="dot" style="background:#27c93f"></div></div>
<div class="tbody">
<span class="prompt">$</span> rulesmith lint --rules resource-leak .../OneDriveConnectorService.java<br/>
<span class="warn">warning[resource-leak]</span>: `outputStream` (OutputStream) is never closed<br/>
<span class="out">  --> OneDriveConnectorService.java:392</span><br/>
<span class="out">   = note: no close() call found and the resource does not escape the method</span>
</div>
</div>

The flagship — post-dominance proves close() is on no path. And it `--fix`es.

<!-- Real file 5/5. Ties back to Beat 5 autofix. -->

---

<!-- _class: lead -->

### The whole thing in one line

# CLAUDE.md is read.
# RuleSmith is run.

<div style="display:flex; gap:18px; margin-top:24px;">
<div class="card"><strong>114 rules</strong> implemented</div>
<div class="card"><strong>typestate · purity · concurrency</strong> beyond SonarQube</div>
<div class="card"><strong>0</strong> API keys to run</div>
</div>

<div style="color:#555; font-size:0.7em; margin-top:22px;">
tree-sitter + CFG/dominance + claude -p · catalog mined from Checker Framework, Effective Java, NASA Power of Ten, OWASP, FP literature
</div>

<!--
Close, 30s. The differentiator: the rules that matter are the ones standard tools
miss, and an English description compiles to one. Cheat sheet:
- Beat 1: examples/java/PaymentGateway.java (5) vs java-fixed (0)
- Star real catch: DefaultStrategy.java:69 atomic-get-set-race
- Others: FtpClientImpl tell-dont-ask/cqs, FtpConnectorService throw-catch, OneDrive leak
-->

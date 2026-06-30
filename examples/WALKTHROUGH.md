# Walkthrough — the rules SonarQube doesn't run

`examples/java/PaymentGateway.java` has five defects that standard linters miss —
each needs typestate, purity, lock-state, or closure reasoning, not a syntax
pattern. `examples/java-fixed/` is the same code repaired (lints clean).

```
alias rulesmith='python -m rulesmith.cli'
FIVE=builder-terminal-before-setters,pure-method-no-side-effects,guarded-by-lock-held,blocking-call-while-holding-lock,lambda-captures-mutable-state
```

## The five (each beyond SonarQube/PMD)

| Rule | Defect | Why a text rule misses it |
|------|--------|----------------------------|
| builder-terminal-before-setters | setter runs after `build()` | *typestate* — tracks call ordering |
| guarded-by-lock-held | `@GuardedBy` field read without the lock | needs lock-state + dominance |
| blocking-call-while-holding-lock | `Future.get()` inside `synchronized` | deadlock reasoning |
| pure-method-no-side-effects | `@Pure` method mutates state | purity via call graph |
| lambda-captures-mutable-state | lambda mutates captured array | escape + capture analysis |

## Step 0 — see them
```
$ rulesmith lint --rules $FIVE examples/java
warning[builder-terminal-before-setters]: 'b' finalized by build() before setter total()
warning[guarded-by-lock-held]: @GuardedBy field 'balance' read without the lock
warning[blocking-call-while-holding-lock]: fut.get() blocks while holding a lock
warning[pure-method-no-side-effects]: @Pure method calls a mutating method
warning[lambda-captures-mutable-state]: lambda mutates captured array 'acc'
5 findings
```

## Step 1 — repair the design, not the syntax
```
$ rulesmith lint --rules $FIVE examples/java-fixed
0 findings
```

Setters before build(); field read under its lock; Future resolved outside the
monitor; a genuinely pure method; a fold instead of a mutating closure. These are
design-level fixes — exactly what a prose CLAUDE.md rule can describe but never
enforce.

## Want the differentiated checks on real code?
See `examples/real-world/` and `demo/NOTES.md` — e.g. a genuine
`atomic-get-set-race` (`textBB.set(textBB.get()==null?…)`) caught in production.

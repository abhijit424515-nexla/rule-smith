# Real-world examples

Unmodified production files from backend-connectors, vendored here so the
findings are reproducible without the full repo. RuleSmith runs on them with no
special setup:

```
rulesmith lint examples/real-world
```

| File | Subsystem | Findings | Distinct rules | Notable flow-sensitive catch |
|------|-----------|----------|----------------|------------------------------|
| `PineconeHelper.java` | vectordb probe | 28 | 14 | generic `catch (Exception)` swallowing errors |
| `ExcelFileWriter.java` | parsers/writer | 62 | 13 | `StringWriter` never closed |
| `TimestampModeProcessor.java` | jdbc source | 18 | 14 | `result` dereferenced without a dominating null guard |
| `XmlUtils.java` | xml parser | 48 | 13 | `(Map) el` downcast not guarded by an instanceof |
| `SQLScriptExecutor.java` | script-runner | 80 | 15 | 15 catch blocks that swallow or over-broaden exceptions |

These are real, not crafted: the leak, the null-deref, and the unchecked cast are
all in shipped code, and each finding cites the graph fact in its `= note:` line.
Run with `--judge` to let claude -p filter name-heuristic false positives, or
`--rules <id>` to focus on one check.

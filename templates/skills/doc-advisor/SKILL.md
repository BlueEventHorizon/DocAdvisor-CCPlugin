---
name: doc-advisor
description: Update document search index (ToC) after modifying, creating, or deleting markdown files in rules/ or specs/ directories.
allowed-tools: Bash, Read, Task
user-invocable: true
---

# doc-advisor

Generate/update ToC (Table of Contents) for AI-searchable document index.

## Usage

```
/doc-advisor <action> [--full]
```

| Argument | Description |
|----------|-------------|
| `$0` | Action: `make-rules-toc` or `make-specs-toc` |
| `$1` | Option: `--full` for full rebuild (default: incremental) |

## Execution Flow

Based on `$0`, execute the corresponding workflow:

### If $0 = "make-rules-toc"

1. Read `.claude/doc-advisor/docs/rules_orchestrator.md` for orchestrator workflow
2. Read `.claude/doc-advisor/docs/rules_toc_format.md` for format definition
3. Execute Phase 1-3 as described in the orchestrator document

### If $0 = "make-specs-toc"

1. Read `.claude/doc-advisor/docs/specs_orchestrator.md` for orchestrator workflow
2. Read `.claude/doc-advisor/docs/specs_toc_format.md` for format definition
3. Execute Phase 1-3 as described in the orchestrator document

## Error Handling

If `$0` is not `make-rules-toc` or `make-specs-toc`:

```
❌ Invalid action: $0
Usage: /doc-advisor <make-rules-toc|make-specs-toc> [--full]
```

---
name: merge-rules-toc
description: Merges completed YAML entries from .claude/doc-advisor/rules/.toc_work/ and generates/validates rules_toc.yaml. Used in Phase 3 merge processing of rules_toc updates.
allowed-tools: Bash, Read
user-invocable: true
---

# merge-rules-toc

Merges completed YAML files from .claude/doc-advisor/rules/.toc_work/ and generates/validates .claude/doc-advisor/rules/rules_toc.yaml.

## Use Cases

- Phase 1 of `/create-rules_toc` (pending YAML generation)
- Phase 3 of `/create-rules_toc` (merge processing)
- Manual execution of pending YAML generation or merge only

## Script List

| Script | Purpose |
|--------|---------|
| `create_pending_yaml.py` | Phase 1: Generate pending YAML templates |
| `merge_rules_toc.py` | Phase 3: Merge processing |
| `validate_rules_toc.py` | Phase 3: Validation processing |

## Commands

### Phase 1: Pending YAML Generation

```bash
# Full mode (all files)
python3 .claude/skills/merge-rules-toc/create_pending_yaml.py --full

# Incremental mode (changed files only)
python3 .claude/skills/merge-rules-toc/create_pending_yaml.py
```

### Phase 3: Merge & Validation

```bash
# Full mode (new generation)
python3 .claude/skills/merge-rules-toc/merge_rules_toc.py --mode full --cleanup
python3 .claude/skills/merge-rules-toc/validate_rules_toc.py

# Incremental mode (differential merge)
python3 .claude/skills/merge-rules-toc/merge_rules_toc.py --mode incremental --cleanup
python3 .claude/skills/merge-rules-toc/validate_rules_toc.py

# Delete-only mode (deletions only, no .toc_work/ needed)
python3 .claude/skills/merge-rules-toc/merge_rules_toc.py --delete-only
python3 .claude/skills/merge-rules-toc/validate_rules_toc.py
```

## Options

| Option | Description |
|--------|-------------|
| `--mode full` | Generate all entries from scratch (default) |
| `--mode incremental` | Differential merge into existing rules_toc.yaml |
| `--delete-only` | Execute deletions only (no .toc_work/ needed, detects deletions via checksum comparison) |
| `--cleanup` | Delete `.toc_work/` directory after successful merge |

## Script Behavior

### Full Mode (Default)

1. Read `.claude/doc-advisor/rules/.toc_work/*.yaml`
2. Remove `_meta` section from each file
3. Extract only entries with `status: completed`
4. Merge into `docs` section using `source_file` as key
5. Generate `.claude/doc-advisor/rules/rules_toc.yaml`

### Incremental Mode

1. Read existing `.claude/doc-advisor/rules/rules_toc.yaml`
2. Detect deleted files via checksum comparison and remove corresponding entries
3. Overwrite/add entries from `.toc_work/*.yaml`
4. Write to `.claude/doc-advisor/rules/rules_toc.yaml`

### Delete-only Mode

1. Read existing `.claude/doc-advisor/rules/rules_toc.yaml`
2. Detect deleted files via checksum comparison
3. Remove corresponding entries
4. Write to `.claude/doc-advisor/rules/rules_toc.yaml`

※ `.toc_work/` directory is not required

## Prerequisites

- **Full/Incremental Mode**: YAML files with completed status must exist in `.claude/doc-advisor/rules/.toc_work/`
- **Delete-only Mode**: `.claude/doc-advisor/rules/.toc_checksums.yaml` must exist
- Python 3 must be available (uses standard library only)

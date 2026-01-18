---
name: merge-specs-toc
description: Merges completed YAML entries from specs/.toc_work/ and generates/validates specs_toc.yaml. Used in Phase 3 merge processing of specs_toc updates.
allowed-tools: Bash, Read
user-invocable: true
---

# merge-specs-toc

Merges completed YAML files from specs/.toc_work/ and generates/validates specs/specs_toc.yaml.

## Use Cases

- Phase 1 of `/create-specs_toc` (pending YAML generation)
- Phase 3 of `/create-specs_toc` (merge processing)
- Manual execution of pending YAML generation or merge only

## Script List

| Script | Purpose |
|--------|---------|
| `create_pending_yaml.py` | Phase 1: Generate pending YAML templates |
| `merge_specs_toc.py` | Phase 3: Merge processing |
| `validate_specs_toc.py` | Phase 3: Validation processing |

## Commands

### Phase 1: Pending YAML Generation

```bash
# Full mode (all files)
python3 skills/merge-specs-toc/create_pending_yaml.py --full

# Incremental mode (changed files only)
python3 skills/merge-specs-toc/create_pending_yaml.py
```

### Phase 3: Merge & Validation

```bash
# Full mode (new generation)
python3 skills/merge-specs-toc/merge_specs_toc.py --mode full --cleanup
python3 skills/merge-specs-toc/validate_specs_toc.py

# Incremental mode (differential merge)
python3 skills/merge-specs-toc/merge_specs_toc.py --mode incremental --cleanup
python3 skills/merge-specs-toc/validate_specs_toc.py

# Delete-only mode (deletions only, no .toc_work/ needed)
python3 skills/merge-specs-toc/merge_specs_toc.py --delete-only
python3 skills/merge-specs-toc/validate_specs_toc.py
```

## Options

| Option | Description |
|--------|-------------|
| `--mode full` | Generate all entries from scratch (default) |
| `--mode incremental` | Differential merge into existing specs_toc.yaml |
| `--delete-only` | Execute deletions only (no .toc_work/ needed, detects deletions via checksum comparison) |
| `--cleanup` | Delete `.toc_work/` directory after successful merge |

## Script Behavior

### Full Mode (Default)

1. Read `specs/.toc_work/*.yaml` (excluding `_deleted.txt`)
2. Parse `_meta` section of each file
3. Extract only entries with `status: completed`
4. Route by `_meta.doc_type`:
   - `spec` → specs section
   - `design` → designs section
5. Auto-generate features (aggregate encountered feature names)
6. Generate `specs/specs_toc.yaml`

### Incremental Mode

1. Read existing `specs/specs_toc.yaml`
2. Detect deleted files via checksum comparison and remove corresponding entries
3. Overwrite/add entries from `.toc_work/*.yaml`
4. Update features (add new features, remove empty features)
5. Write to `specs/specs_toc.yaml`

### Delete-only Mode

1. Read existing `specs/specs_toc.yaml`
2. Detect deleted files via checksum comparison
3. Remove corresponding entries
4. Remove empty features
5. Write to `specs/specs_toc.yaml`

※ `.toc_work/` directory is not required

## Prerequisites

- **Full/Incremental Mode**: YAML files with completed status must exist in `specs/.toc_work/`
- **Delete-only Mode**: `specs/.toc_checksums.yaml` must exist
- Python 3 must be available (uses standard library only)

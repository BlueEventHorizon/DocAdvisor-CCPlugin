---
name: create-toc-checksums
description: Calculates hash values for all .md files under rules/ or specs/ and generates/updates .toc_checksums.yaml. Used for incremental mode change detection.
allowed-tools: Bash, Read
user-invocable: true
---

# create-toc-checksums

Calculates hash values for all .md files under rules/ or specs/ and generates .toc_checksums.yaml.

## Use Cases

- After completing full mode of `/create-rules_toc`
- After completing full mode of `/create-specs_toc`
- Preparation for incremental mode change detection

## Commands

```bash
# For rules
python3 skills/create-toc-checksums/create_checksums.py --target rules

# For specs
python3 skills/create-toc-checksums/create_checksums.py --target specs
```

## Output Files

### For rules: `rules/.toc_checksums.yaml`

```yaml
# Checksum file for rules_toc.yaml
# Auto-generated - DO NOT EDIT MANUALLY
generated_at: 2026-01-16T12:00:00Z
file_count: 30
checksums:
  core/architecture_rule.md: a1b2c3d4e5f6...
  core/coding_rule.md: b2c3d4e5f6a1...
  ...
```

### For specs: `specs/.toc_checksums.yaml`

```yaml
# Checksum file for specs_toc.yaml
# Auto-generated - DO NOT EDIT MANUALLY
generated_at: 2026-01-16T12:00:00Z
file_count: 50
checksums:
  main/requirements/screens/SCR-001_xxx.md: a1b2c3d4e5f6...
  main/design/DES-001_xxx.md: b2c3d4e5f6a1...
  ...
```

## Script Behavior

1. Load configuration based on specified `--target` (rules/specs)
2. Search all `.md` files under target directory (applying exclude patterns)
3. Calculate SHA-256 hash for each file
4. Generate checksum file with relative path as key

## Usage in Incremental Mode

1. If `.toc_checksums.yaml` exists, incremental mode is enabled
2. Compare current hash of each file with stored hash
3. Only process files with changes
4. After processing, run this script to generate new checksums

## Prerequisites

- Python 3 must be available (uses standard library only)
- toc-common/config.yaml should exist (defaults are used if missing)

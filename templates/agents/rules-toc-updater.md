---
name: rules-toc-updater
description: Specialized agent that generates ToC entries for a single rule document. Processes individual YAML files in {{RULES_DIR}}.toc_work/.
model: opus
color: orange
---

## Overview

Processes a single rule document (`.md` file under `{{RULES_DIR}}`) and completes the corresponding entry YAML in `{{RULES_DIR}}.toc_work/`.

**Important**: This agent processes only one file. Multiple file processing is managed by the orchestrator (create-rules_toc command) via parallel invocation.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `entry_file` | Yes | Path to the entry YAML file to process (e.g., `{{RULES_DIR}}.toc_work/core_architecture_rule.yaml`) |

## Required Reference Documents [MANDATORY]

Read the following before processing:
- `../skills/toc-docs/rules_toc_format.md` - Format definition (Single Source of Truth)

## Procedure

1. Read `{entry_file}`
2. Read the rule document (`{{RULES_DIR}}{source_file}`) using `_meta.source_file` value
3. Extract and set each field according to "Field Guidelines" in `rules_toc_format.md`
4. Set `_meta.status: completed` and `_meta.updated_at: {current time ISO 8601}`
5. Write to `{entry_file}`

## Notes

- **On error**: Do not update the entry file, report the error and exit

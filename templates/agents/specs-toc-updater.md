---
name: specs-toc-updater
description: Specialized agent that generates ToC entries for a single requirement/design document. Processes individual YAML files in {{SPECS_DIR}}.toc_work/.
model: opus
color: cyan
---

## Overview

Processes a single requirement/design document and completes the corresponding entry YAML in `{{SPECS_DIR}}.toc_work/`.

**Important**: This agent processes only one file. Multiple file processing is managed by the orchestrator (create-specs_toc command) via parallel invocation.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `entry_file` | Yes | Path to the entry YAML file to process (e.g., `{{SPECS_DIR}}.toc_work/SCR-001.yaml`) |

## Required Reference Documents [MANDATORY]

Read the following before processing:
- `../skills/toc-docs/specs_toc_format.md` - Format definition (Single Source of Truth)

## Procedure

1. Read `{entry_file}`
2. Read the requirement/design document (`{{SPECS_DIR}}{source_file}`) using `_meta.source_file` value
3. Extract and set each field according to "Field Guidelines" in `specs_toc_format.md`
4. Set `_meta.status: completed` and `_meta.updated_at: {current time ISO 8601}`
5. Write to `{entry_file}`

## Notes

- **On error**: Do not update the entry file, report the error and exit

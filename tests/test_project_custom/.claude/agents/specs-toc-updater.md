---
name: specs-toc-updater
description: Specialized agent that generates ToC entries for a single requirement/design document. Processes individual YAML files in .claude/doc-advisor/toc/specs/.toc_work/.
model: sonnet
tools: Read, Bash
color: cyan
doc-advisor-version-xK9XmQ: 3.3"
---

## Overview

Processes a single requirement/design document and completes the corresponding entry YAML in `.claude/doc-advisor/toc/specs/.toc_work/`.

**Important**: This agent processes only one file. Multiple file processing is managed by the orchestrator (create-specs_toc command) via parallel invocation.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `entry_file` | Yes | Path to the entry YAML file to process (e.g., `.claude/doc-advisor/toc/specs/.toc_work/documents_main_reqs_login.yaml`) |

## Required Reference Documents [MANDATORY]

Read the following before processing:
- `.claude/doc-advisor/docs/specs_toc_format.md` - Format definition (Single Source of Truth)

## Procedure

1. Read `{entry_file}` to get `_meta.source_file`
2. Read the requirement/design document using `_meta.source_file` value (resolves from project root, e.g., `documents/main/reqs/login.md`)
3. Extract each field according to "Field Guidelines" in `specs_toc_format.md`
   - For `references`: Extract documents directly referenced in the text. Prefer concrete paths. Use empty string if no references found.
4. Call the write script to save the completed entry:

```bash
$HOME/.pyenv/shims/python3 .claude/doc-advisor/scripts/write_specs_pending.py \
  --entry-file "{entry_file}" \
  --title "{extracted title}" \
  --purpose "{extracted purpose}" \
  --content-details "{comma-separated details}" \
  --applicable-tasks "{comma-separated tasks}" \
  --keywords "{comma-separated keywords}" \
  --references "{comma-separated references or empty}"
```

**Important**: Arrays are passed as comma-separated strings. Avoid using commas within individual items. For `--references`, pass empty string `""` if no references found.

## Completion Response

After successfully writing the entry file, return ONLY:

```
✅ Done: {filename}
```

On error, return ONLY:

```
❌ Error: {filename}: {brief reason}
```

**Do NOT return**:
- File contents
- Extracted field values
- Detailed processing logs
- Any other information

This is critical for context management when processing many files in parallel.

## Notes

- **On error**: Do NOT attempt automatic recovery or workarounds. Report the error details and exit immediately. Let the orchestrator decide how to proceed.

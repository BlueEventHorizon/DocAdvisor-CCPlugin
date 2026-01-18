---
name: toc-docs
description: Format definitions and workflow documents for the ToC auto-generation system. Referenced within the plugin.
allowed-tools: []
user-invocable: false
---

# toc-docs

Provides format definitions and workflow documents for the ToC auto-generation system (rules_toc.yaml / specs_toc.yaml).

## Overview

This skill is not invoked directly but is referenced by:

- `commands/create-rules_toc.md` - rules_toc orchestrator
- `commands/create-specs_toc.md` - specs_toc orchestrator
- `agents/rules-toc-updater.md` - rules entry processor
- `agents/specs-toc-updater.md` - specs entry processor

## Provided Files

| File | Purpose |
|------|---------|
| `rules_toc_format.md` | rules_toc.yaml format definition (Single Source of Truth) |
| `specs_toc_format.md` | specs_toc.yaml format definition (Single Source of Truth) |
| `rules_toc_update_workflow.md` | rules_toc update workflow |
| `specs_toc_update_workflow.md` | specs_toc update workflow |

---
name: next-doc-id
description: Gets the next ID for requirements or design documents. Use when creating new requirements (APP-/SCR-/CMP-/FNC-/BL-/NF-/DM-/EXT-/NAV-/THEME-) or design documents (DES-) and need the next sequential ID. Scans all branches to prevent ID collisions.
---

# Get Next Requirement/Design ID

When creating new requirements or design documents, scans all branches (local + remote) to get the next sequential ID.

## When to Use

- Creating a new application overview (APP-)
- Creating a new screen requirement (SCR-)
- Creating a new UI component requirement (CMP-)
- Creating a new functional requirement (FNC-)
- Creating a new business logic requirement (BL-)
- Creating a new non-functional requirement (NF-)
- Creating a new data model requirement (DM-)
- Creating a new external interface requirement (EXT-)
- Creating a new navigation requirement (NAV-)
- Creating a new theme requirement (THEME-)
- Creating a new design document (DES-)

## How to Run

Execute the scan script:

```bash
skills/next-doc-id/scan_ids.sh SCR   # → SCR-016
skills/next-doc-id/scan_ids.sh BL    # → BL-014
skills/next-doc-id/scan_ids.sh DES   # → DES-016
```

## ID System

| Prefix | Category | Example |
|--------|----------|---------|
| APP- | Application Overview | APP-001_foo_app_overview_spec.md |
| SCR- | Screen Requirements | SCR-001_foo_list_screen_spec.md |
| CMP- | UI Components | CMP-001_FooListItem_spec.md |
| FNC- | Functional Requirements | FNC-001_bar_management_spec.md |
| BL- | Business Logic | BL-001_data_sync_persistence_spec.md |
| NF- | Non-functional Requirements | NF-001_debug_features_spec.md |
| DM- | Data Models | DM-001_foo_entity_spec.md |
| EXT- | External Interfaces | EXT-001_external_api_spec.md |
| NAV- | Navigation | NAV-001_main_navigation_spec.md |
| THEME- | Themes | THEME-001_design_tokens_spec.md |
| DES- | Design Documents | DES-001_foo_list_design.md |

## How It Works

1. Identify base branch (develop or main)
2. Scan all branches derived from base branch (local + remote)
3. Detect maximum number for specified prefix
4. Display warning if duplicates found
5. Return maximum number + 1

## Output Example

```
Next ID: SCR-016

Scan Results:
  Base branch: develop
  Branches scanned: 7
  SCR-XXX found: 15 (max: SCR-015)
```

### When Duplicates Exist

```
Next ID: SCR-016

Scan Results:
  Base branch: develop
  Branches scanned: 7
  SCR-XXX found: 15 (max: SCR-015)

⚠️  Duplicates detected (same ID used in different branches):
  SCR-013: feature/edit_pickup, origin/feature/print_letter
  SCR-014: feature/edit_pickup, origin/feature/print_letter
```

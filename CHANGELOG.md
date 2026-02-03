# Changelog

All notable changes to Doc Advisor are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [3.0.0] - 2026-02-03

### Added
- **Skills integration**: doc-advisor is now a Claude Code Skill with `$ARGUMENTS` support
- **Unified command interface**: `/doc-advisor make-rules-toc [--full]` and `/doc-advisor make-specs-toc [--full]`
- **Auto-triggering**: Claude can automatically suggest ToC updates when documents change
- **Orchestrator docs**: `rules_orchestrator.md` and `specs_orchestrator.md` for skill execution flow
- **Upgrade support**: Automatic legacy file cleanup from v2.0

### Changed
- **Directory structure** (major reorganization):
  - `commands/` deprecated and removed (migrated to Skills)
  - `skills/doc-advisor/` now contains only `SKILL.md` (entry point)
  - All resources moved to `doc-advisor/`:
    - `doc-advisor/config.yaml` - configuration
    - `doc-advisor/docs/` - documentation
    - `doc-advisor/scripts/` - Python scripts
  - Runtime output reorganized:
    - `doc-advisor/rules/` → `doc-advisor/toc/rules/`
    - `doc-advisor/specs/` → `doc-advisor/toc/specs/`
- **Command format**:
  - `/create-rules_toc` → `/doc-advisor make-rules-toc`
  - `/create-specs_toc` → `/doc-advisor make-specs-toc`
- **setup.sh behavior**:
  - `agents/` now uses overwrite-only mode (preserves user's custom agents)
  - `skills/doc-advisor/` uses clean install mode (SKILL.md only)
  - `doc-advisor/` resources are copied fresh
  - Legacy files are automatically deleted (file-specific, not directory-wide)
  - `config.yaml` protection with skip/overwrite/merge options

### Structure (v3.0)
```
.claude/
├── agents/
│   ├── rules-advisor.md
│   ├── specs-advisor.md
│   ├── rules-toc-updater.md
│   └── specs-toc-updater.md
├── skills/
│   └── doc-advisor/
│       └── SKILL.md            # Entry point only
└── doc-advisor/
    ├── config.yaml             # Configuration
    ├── docs/                   # Documentation
    ├── scripts/                # Python scripts
    └── toc/                    # Runtime output
        ├── rules/
        │   ├── rules_toc.yaml
        │   ├── .toc_checksums.yaml
        │   └── .toc_work/
        └── specs/
            ├── specs_toc.yaml
            ├── .toc_checksums.yaml
            └── .toc_work/
```

### Removed
- `templates/commands/` directory

### Fixed
- User's custom agents and commands are no longer accidentally deleted during upgrade
- Legacy cleanup no longer incorrectly deletes `doc-advisor/config.yaml` on re-install (was looking for v2.0 legacy in wrong path)

---

## [2.0.0] - 2026-01-25

### Added
- **Project-based setup**: All files copied to target project (no `--plugin-dir` needed)
- **Slash commands**: `/create-rules_toc` and `/create-specs_toc`
- **Parallel processing**: Up to 5 concurrent subagents for ToC generation
- **Incremental updates**: SHA-256 hash-based change detection
- **Interruption recovery**: `.toc_work/` directory preserves partial results
- **Custom directory support**: Configurable rules/specs directory names
- **Agent model selection**: Choose opus/sonnet/haiku/inherit for subagents

### Changed
- Moved from plugin mode to project-based mode
- Configuration file location: `.claude/doc-advisor/config.yaml`
- Documentation location: `.claude/doc-advisor/docs/`

### Structure (v2.0)
```
.claude/
├── commands/
│   ├── create-rules_toc.md
│   └── create-specs_toc.md
├── doc-advisor/
│   ├── config.yaml
│   └── docs/
├── agents/
│   ├── rules-advisor.md
│   ├── specs-advisor.md
│   ├── rules-toc-updater.md
│   └── specs-toc-updater.md
└── skills/
    └── doc-advisor/
        ├── SKILL.md
        └── scripts/
```

---

## [1.0.0] - 2026-01-20

### Added
- **Initial release**
- **Plugin mode**: Run with `claude --plugin-dir /path/to/DocAdvisor-CC`
- **Basic ToC generation**: Parse `.md` files and generate YAML index
- **Document categories**: rules (development docs) and specs (requirements/design)
- **doc_type detection**: Automatic detection based on directory path
- **Advisor agents**: rules-advisor and specs-advisor for document lookup

### Structure (v1.x)
```
DocAdvisor-CC/  (plugin directory)
├── commands/
│   ├── create-rules_toc.md
│   └── create-specs_toc.md
├── agents/
│   └── ...
└── skills/
    └── doc-advisor/
        └── scripts/
```

---

## Version Comparison

| Feature | v1.x | v2.0 | v3.0 |
|---------|------|------|------|
| Installation | Plugin mode | Project-based | Project-based |
| Commands | `/create-*_toc` | `/create-*_toc` | `/doc-advisor make-*-toc` |
| Config location | Plugin dir | `.claude/doc-advisor/` | `.claude/doc-advisor/` |
| Docs/Scripts location | Plugin dir | `.claude/doc-advisor/` | `.claude/doc-advisor/` |
| ToC output location | Plugin dir | `.claude/doc-advisor/rules/` | `.claude/doc-advisor/toc/rules/` |
| Auto-trigger | No | No | Yes |
| Parallel processing | No | Yes | Yes |
| Incremental updates | No | Yes | Yes |
| Custom directories | No | Yes | Yes |
| Upgrade support | - | - | Yes |

---

## Upgrade Path

### v2.0 → v3.0

Run `setup.sh` on your project:

```bash
./setup.sh /path/to/your-project
```

**Automatic changes:**
- Legacy commands deleted: `commands/create-rules_toc.md`, `commands/create-specs_toc.md`
- `skills/doc-advisor/` cleaned (only SKILL.md remains)
- `doc-advisor/docs/` and `doc-advisor/scripts/` updated
- ToC output moved: `doc-advisor/rules/` → `doc-advisor/toc/rules/`
- ToC output moved: `doc-advisor/specs/` → `doc-advisor/toc/specs/`

**Preserved:**
- Your custom commands in `commands/`
- Your custom agents in `agents/`
- Your `config.yaml` settings (with skip/overwrite/merge options)

**Note:** After upgrade, regenerate ToC files:
```bash
/doc-advisor make-rules-toc --full
/doc-advisor make-specs-toc --full
```

### v1.x → v3.0

1. Remove plugin mode usage (`--plugin-dir` flag)
2. Run `setup.sh` on your project
3. Regenerate ToC with new commands:
   ```bash
   /doc-advisor make-rules-toc --full
   /doc-advisor make-specs-toc --full
   ```

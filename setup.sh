#!/bin/bash
# Doc Advisor Setup Script (v3.0)
#
# Copies all templates to target project and creates configuration
#
# Usage:
#   ./setup.sh TARGET_DIR    # Setup for specified project
#   ./setup.sh               # Interactive mode (prompts for directory)
#   ./setup.sh -h, --help    # Show help

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory (plugin root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAST_SETUP_FILE="${SCRIPT_DIR}/.last_setup"

# Default values (no trailing slash)
DEFAULT_RULES_DIR="rules"
DEFAULT_SPECS_DIR="specs"
# Subdirectory names for specs (doc_type mapping)
DEFAULT_REQUIREMENT_DIR_NAME="requirements"
DEFAULT_DESIGN_DIR_NAME="design"
DEFAULT_PLAN_DIR_NAME="plan"
# Agent model (opus, sonnet, haiku, inherit)
DEFAULT_AGENT_MODEL="opus"

# Load previous settings if available
if [[ -f "$LAST_SETUP_FILE" ]]; then
    source "$LAST_SETUP_FILE"
    # Use saved values as defaults
    DEFAULT_TARGET_DIR="${LAST_TARGET_DIR:-}"
    DEFAULT_RULES_DIR="${LAST_RULES_DIR:-$DEFAULT_RULES_DIR}"
    DEFAULT_SPECS_DIR="${LAST_SPECS_DIR:-$DEFAULT_SPECS_DIR}"
    DEFAULT_REQUIREMENT_DIR_NAME="${LAST_REQUIREMENT_DIR_NAME:-$DEFAULT_REQUIREMENT_DIR_NAME}"
    DEFAULT_DESIGN_DIR_NAME="${LAST_DESIGN_DIR_NAME:-$DEFAULT_DESIGN_DIR_NAME}"
    DEFAULT_PLAN_DIR_NAME="${LAST_PLAN_DIR_NAME:-$DEFAULT_PLAN_DIR_NAME}"
    DEFAULT_AGENT_MODEL="${LAST_AGENT_MODEL:-$DEFAULT_AGENT_MODEL}"
fi

# Parse arguments
TARGET_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            echo "Doc Advisor Setup Script (v3.0)"
            echo ""
            echo "Usage:"
            echo "  ./setup.sh TARGET_DIR    # Setup for specified project"
            echo "  ./setup.sh               # Interactive mode (prompts for directory)"
            echo "  ./setup.sh -h, --help    # Show help"
            echo ""
            echo "This script creates:"
            echo "  TARGET_DIR/.claude/agents/         # Agent definitions"
            echo "  TARGET_DIR/.claude/skills/         # Skill modules (inc. doc-advisor)"
            echo "  TARGET_DIR/.claude/doc-advisor/    # Runtime output (ToC files)"
            echo ""
            echo "Default directories:"
            echo "  Rules: ${DEFAULT_RULES_DIR}"
            echo "  Specs: ${DEFAULT_SPECS_DIR}"
            exit 0
            ;;
        -*)
            echo "Error: Unknown option: $1"
            echo "Run ./setup.sh --help for usage information"
            exit 1
            ;;
        *)
            if [[ -z "$TARGET_DIR" ]]; then
                TARGET_DIR="$1"
            else
                echo "Error: Too many arguments"
                echo "Run ./setup.sh --help for usage information"
                exit 1
            fi
            shift
            ;;
    esac
done

# Interactive prompt if not specified
if [[ -z "$TARGET_DIR" ]]; then
    echo "Doc Advisor Setup Script (v3.0)"
    echo ""
    if [[ -n "$DEFAULT_TARGET_DIR" ]]; then
        read -p "Enter target project directory [${DEFAULT_TARGET_DIR}]: " TARGET_DIR
        TARGET_DIR="${TARGET_DIR:-$DEFAULT_TARGET_DIR}"
    else
        read -p "Enter target project directory: " TARGET_DIR
    fi
    if [[ -z "$TARGET_DIR" ]]; then
        echo "Error: Target directory is required"
        exit 1
    fi
fi

# Expand ~ and relative paths
TARGET_DIR="$(eval echo "$TARGET_DIR")"
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)" || {
    echo "Error: Directory does not exist: $TARGET_DIR"
    exit 1
}

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Doc Advisor Setup (v3.0)${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "Target project: ${TARGET_DIR}"
echo ""

# Interactive prompts for directories
echo "Configure document directories for your project."
echo "(Press Enter to use default value)"
echo ""

read -p "Rules directory [${DEFAULT_RULES_DIR}]: " RULES_DIR
RULES_DIR="${RULES_DIR:-$DEFAULT_RULES_DIR}"

read -p "Specs directory [${DEFAULT_SPECS_DIR}]: " SPECS_DIR
SPECS_DIR="${SPECS_DIR:-$DEFAULT_SPECS_DIR}"

echo ""
echo "Configure subdirectory names for specs:"

read -p "  Requirements directory name [${DEFAULT_REQUIREMENT_DIR_NAME}]: " REQUIREMENT_DIR_NAME
REQUIREMENT_DIR_NAME="${REQUIREMENT_DIR_NAME:-$DEFAULT_REQUIREMENT_DIR_NAME}"

read -p "  Design directory name [${DEFAULT_DESIGN_DIR_NAME}]: " DESIGN_DIR_NAME
DESIGN_DIR_NAME="${DESIGN_DIR_NAME:-$DEFAULT_DESIGN_DIR_NAME}"

read -p "  Plan directory name [${DEFAULT_PLAN_DIR_NAME}]: " PLAN_DIR_NAME
PLAN_DIR_NAME="${PLAN_DIR_NAME:-$DEFAULT_PLAN_DIR_NAME}"

echo ""
echo "Configure agent model (opus, sonnet, haiku, inherit):"
read -p "  Agent model [${DEFAULT_AGENT_MODEL}]: " AGENT_MODEL
AGENT_MODEL="${AGENT_MODEL:-$DEFAULT_AGENT_MODEL}"

# Validate agent model
case "$AGENT_MODEL" in
    opus|sonnet|haiku|inherit)
        ;;
    *)
        echo -e "${RED}Warning: Unknown model '$AGENT_MODEL'. Using 'opus' as default.${NC}"
        AGENT_MODEL="opus"
        ;;
esac

# Remove trailing slash if present (placeholders should not include trailing slash)
RULES_DIR="${RULES_DIR%/}"
SPECS_DIR="${SPECS_DIR%/}"

# Detect Python path
# Check if shell wrapper exists (e.g., Claude Code shell-snapshots directory)
if [[ -d "$HOME/.claude/shell-snapshots" ]] && [[ -n "$(ls -A "$HOME/.claude/shell-snapshots" 2>/dev/null)" ]]; then
    # Shell wrapper likely present: use full path to bypass
    PYTHON_PATH=$(/usr/bin/which python3 2>/dev/null || echo "python3")
    # Replace $HOME with $HOME variable (expands at runtime)
    PYTHON_PATH="${PYTHON_PATH/#$HOME/\$HOME}"
    PYTHON_WRAPPED="yes"
else
    # No wrapper detected: use simple command
    PYTHON_PATH="python3"
    PYTHON_WRAPPED="no"
fi

echo ""
echo "Configuration:"
echo -e "  RULES_DIR: ${BLUE}${RULES_DIR}${NC}"
echo -e "  SPECS_DIR: ${BLUE}${SPECS_DIR}${NC}"
echo -e "  REQUIREMENT_DIR_NAME: ${BLUE}${REQUIREMENT_DIR_NAME}${NC}"
echo -e "  DESIGN_DIR_NAME: ${BLUE}${DESIGN_DIR_NAME}${NC}"
echo -e "  PLAN_DIR_NAME: ${BLUE}${PLAN_DIR_NAME}${NC}"
echo -e "  AGENT_MODEL: ${BLUE}${AGENT_MODEL}${NC}"
echo -e "  PYTHON_PATH: ${BLUE}${PYTHON_PATH}${NC}"
if [[ "$PYTHON_WRAPPED" == "yes" ]]; then
    echo -e "    ${RED}(python3 may be wrapped: using explicit path for reliability)${NC}"
fi
echo ""

# Create directories
CLAUDE_DIR="${TARGET_DIR}/.claude"
DOC_ADVISOR_DIR="${CLAUDE_DIR}/doc-advisor"
AGENTS_DIR="${CLAUDE_DIR}/agents"
SKILLS_DIR="${CLAUDE_DIR}/skills"

# =============================================================================
# Clean up legacy files from v2.0 (file-specific deletion)
# NOTE: This uses file-name-based deletion because v2.0 has no identifiers.
#       After identifier system is introduced, this code should be removed
#       and replaced with identifier-based deletion.
# =============================================================================
LEGACY_CLEANED=0

# commands/ - delete only doc-advisor commands (preserve user's custom commands)
if [[ -f "${CLAUDE_DIR}/commands/create-rules_toc.md" ]]; then
    rm -f "${CLAUDE_DIR}/commands/create-rules_toc.md"
    echo -e "${GREEN}Removed legacy: commands/create-rules_toc.md${NC}"
    LEGACY_CLEANED=1
fi
if [[ -f "${CLAUDE_DIR}/commands/create-specs_toc.md" ]]; then
    rm -f "${CLAUDE_DIR}/commands/create-specs_toc.md"
    echo -e "${GREEN}Removed legacy: commands/create-specs_toc.md${NC}"
    LEGACY_CLEANED=1
fi

# v2.0 had config/docs/scripts in skills/doc-advisor/ - migrate if found
LEGACY_SKILL_CONFIG="${SKILLS_DIR}/doc-advisor/config.yaml"
if [[ -f "$LEGACY_SKILL_CONFIG" ]]; then
    # Backup v2.0 config for potential migration
    cp "$LEGACY_SKILL_CONFIG" "${SKILLS_DIR}/config.yaml.legacy.tmp"
    MIGRATE_LEGACY_CONFIG=1
    rm -f "$LEGACY_SKILL_CONFIG"
    echo -e "${GREEN}Removed legacy: skills/doc-advisor/config.yaml (will migrate)${NC}"
    LEGACY_CLEANED=1
fi
if [[ -d "${SKILLS_DIR}/doc-advisor/docs" ]]; then
    rm -rf "${SKILLS_DIR}/doc-advisor/docs"
    echo -e "${GREEN}Removed legacy: skills/doc-advisor/docs/${NC}"
    LEGACY_CLEANED=1
fi
if [[ -d "${SKILLS_DIR}/doc-advisor/scripts" ]]; then
    rm -rf "${SKILLS_DIR}/doc-advisor/scripts"
    echo -e "${GREEN}Removed legacy: skills/doc-advisor/scripts/${NC}"
    LEGACY_CLEANED=1
fi

# v3.0 moved docs to doc-advisor/ - clean old docs directory if it exists with outdated files
# (scripts and config are handled by the copy process, only docs/ needs explicit cleanup)
if [[ -d "${DOC_ADVISOR_DIR}/docs" ]]; then
    rm -rf "${DOC_ADVISOR_DIR}/docs"
    LEGACY_CLEANED=1
fi

if [[ $LEGACY_CLEANED -eq 1 ]]; then
    echo ""
fi

mkdir -p "${DOC_ADVISOR_DIR}"
mkdir -p "${DOC_ADVISOR_DIR}/toc/rules"    # ToC/checksums for rules
mkdir -p "${DOC_ADVISOR_DIR}/toc/specs"    # ToC/checksums for specs
mkdir -p "${AGENTS_DIR}"
mkdir -p "${SKILLS_DIR}"

# Function to copy and substitute variables in a file
copy_and_substitute() {
    local src="$1"
    local dst="$2"

    if [[ -f "$src" ]]; then
        # Perform variable substitution
        sed -e "s|{{RULES_DIR}}|${RULES_DIR}|g" \
            -e "s|{{SPECS_DIR}}|${SPECS_DIR}|g" \
            -e "s|{{REQUIREMENT_DIR_NAME}}|${REQUIREMENT_DIR_NAME}|g" \
            -e "s|{{DESIGN_DIR_NAME}}|${DESIGN_DIR_NAME}|g" \
            -e "s|{{PLAN_DIR_NAME}}|${PLAN_DIR_NAME}|g" \
            -e "s|{{AGENT_MODEL}}|${AGENT_MODEL}|g" \
            -e "s|{{PYTHON_PATH}}|${PYTHON_PATH}|g" \
            "$src" > "$dst"
    fi
}

# Function to copy directory recursively with variable substitution
copy_dir_with_substitution() {
    local src_dir="$1"
    local dst_dir="$2"

    if [[ ! -d "$src_dir" ]]; then
        echo -e "${RED}Warning: Source directory not found: ${src_dir}${NC}"
        return
    fi

    # Create destination directory
    mkdir -p "$dst_dir"

    # Copy files with substitution
    find "$src_dir" -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.py" -o -name "*.sh" \) | while read -r src_file; do
        # Get relative path from source directory
        rel_path="${src_file#$src_dir/}"
        dst_file="${dst_dir}/${rel_path}"

        # Create parent directory if needed
        mkdir -p "$(dirname "$dst_file")"

        # Copy with substitution for text files
        if [[ "$src_file" == *.md ]] || [[ "$src_file" == *.yaml ]]; then
            copy_and_substitute "$src_file" "$dst_file"
        else
            # Copy as-is for Python and shell scripts
            cp "$src_file" "$dst_file"
        fi
    done

    # Make shell scripts executable
    find "$dst_dir" -name "*.sh" -type f -exec chmod +x {} \;
}

echo "Copying templates..."
echo ""

# Check if config.yaml already exists (user may have customized it)
EXISTING_CONFIG="${DOC_ADVISOR_DIR}/config.yaml"
SKIP_CONFIG=0

if [[ -f "$EXISTING_CONFIG" ]]; then
    echo -e "${YELLOW}Existing config.yaml found: ${EXISTING_CONFIG}${NC}"
    echo "  This file may contain your custom settings (exclude patterns, etc.)."
    echo ""
    echo "  Options:"
    echo "    [o] Overwrite (backup to config.yaml.bak)"
    echo "    [s] Skip (keep existing config)"
    echo "    [m] Merge manually (show diff after setup)"
    read -p "  Choice [s]: " CONFIG_CHOICE
    CONFIG_CHOICE="${CONFIG_CHOICE:-s}"

    case "$CONFIG_CHOICE" in
        [Oo])
            # Backup to skills/ dir (outside doc-advisor/ which will be deleted)
            cp "$EXISTING_CONFIG" "${SKILLS_DIR}/config.yaml.bak.tmp"
            RESTORE_BAK=1
            echo -e "${GREEN}  Backup will be created: config.yaml.bak${NC}"
            ;;
        [Mm])
            cp "$EXISTING_CONFIG" "${SKILLS_DIR}/config.yaml.old.tmp"
            SHOW_CONFIG_DIFF=1
            ;;
        *)
            SKIP_CONFIG=1
            echo -e "${BLUE}  Keeping existing config.yaml${NC}"
            ;;
    esac
    echo ""
fi

# Copy agents (overwrite only - preserve user's custom agents)
echo "  agents/ ..."
if [[ -d "${AGENTS_DIR}" ]]; then
    # doc-advisor managed agents (will be overwritten)
    MANAGED_AGENTS="rules-advisor.md specs-advisor.md rules-toc-updater.md specs-toc-updater.md"
    # Check for non-managed agents and notify user
    for agent in "${AGENTS_DIR}"/*.md; do
        [[ -e "$agent" ]] || continue
        name=$(basename "$agent")
        if ! echo "$MANAGED_AGENTS" | grep -qw "$name"; then
            echo -e "${BLUE}    Preserving: $name${NC}"
        fi
    done
fi
copy_dir_with_substitution "${SCRIPT_DIR}/templates/agents" "${AGENTS_DIR}"

# Copy skills/doc-advisor/SKILL.md (entry point only)
echo "  skills/doc-advisor/ ..."
DOC_ADVISOR_SKILL_DIR="${SKILLS_DIR}/doc-advisor"

# Clean and copy SKILL.md only
if [[ -d "${DOC_ADVISOR_SKILL_DIR}" ]]; then
    rm -rf "${DOC_ADVISOR_SKILL_DIR}"
fi
mkdir -p "${DOC_ADVISOR_SKILL_DIR}"
copy_and_substitute "${SCRIPT_DIR}/templates/skills/doc-advisor/SKILL.md" "${DOC_ADVISOR_SKILL_DIR}/SKILL.md"

# Copy doc-advisor resources (config, docs, scripts)
echo "  doc-advisor/ ..."

# Backup config to temp location if skipping
if [[ $SKIP_CONFIG -eq 1 ]]; then
    cp "$EXISTING_CONFIG" "${DOC_ADVISOR_DIR}/config.yaml.tmp"
fi

# Copy templates/doc-advisor/ to .claude/doc-advisor/
copy_dir_with_substitution "${SCRIPT_DIR}/templates/doc-advisor" "${DOC_ADVISOR_DIR}"

# Restore config if skipped
if [[ $SKIP_CONFIG -eq 1 ]]; then
    mv "${DOC_ADVISOR_DIR}/config.yaml.tmp" "$EXISTING_CONFIG"
fi

# Move backup to final location (overwrite mode)
if [[ "${RESTORE_BAK:-0}" == "1" ]] && [[ -f "${SKILLS_DIR}/config.yaml.bak.tmp" ]]; then
    mv "${SKILLS_DIR}/config.yaml.bak.tmp" "${EXISTING_CONFIG}.bak"
fi

# Show diff if requested (merge mode)
if [[ "${SHOW_CONFIG_DIFF:-0}" == "1" ]] && [[ -f "${SKILLS_DIR}/config.yaml.old.tmp" ]]; then
    mv "${SKILLS_DIR}/config.yaml.old.tmp" "${EXISTING_CONFIG}.old"
    echo ""
    echo -e "${YELLOW}Config diff (old vs new):${NC}"
    diff "${EXISTING_CONFIG}.old" "$EXISTING_CONFIG" || true
    echo ""
    echo -e "${YELLOW}Old config saved as: ${EXISTING_CONFIG}.old${NC}"
fi

echo ""
echo "Generated configuration:"
echo "  ${DOC_ADVISOR_DIR}/config.yaml"

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Setup Complete${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "Files created at:"
echo "  ${CLAUDE_DIR}/"
echo "    agents/            # Agent definitions"
echo "    skills/            # Skill modules (inc. doc-advisor)"
echo "    doc-advisor/       # Runtime output (ToC files)"
# Save settings for next run
cat > "$LAST_SETUP_FILE" << EOF
# Last setup settings (auto-generated)
LAST_TARGET_DIR="${TARGET_DIR}"
LAST_RULES_DIR="${RULES_DIR}"
LAST_SPECS_DIR="${SPECS_DIR}"
LAST_REQUIREMENT_DIR_NAME="${REQUIREMENT_DIR_NAME}"
LAST_DESIGN_DIR_NAME="${DESIGN_DIR_NAME}"
LAST_PLAN_DIR_NAME="${PLAN_DIR_NAME}"
LAST_AGENT_MODEL="${AGENT_MODEL}"
EOF

echo ""
echo "Next steps:"
echo -e "  1. Verify ${BLUE}${RULES_DIR}${NC} and ${BLUE}${SPECS_DIR}${NC} directories exist in your project"
echo "  2. Start Claude Code:"
echo -e "     cd ${BLUE}${TARGET_DIR}${NC}"
echo "     claude"
echo -e "  3. Run ${YELLOW}/doc-advisor make-rules-toc --full${NC} for initial ToC generation"
echo -e "  4. Run ${YELLOW}/doc-advisor make-specs-toc --full${NC} for initial ToC generation"
echo ""

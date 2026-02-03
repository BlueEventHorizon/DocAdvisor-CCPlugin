#!/bin/bash
# Test script for setup.sh upgrade scenarios
# Tests: legacy file deletion, config.yaml handling, agent preservation
# Usage: ./test_setup_upgrade.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_PROJECT="$SCRIPT_DIR/test_project_upgrade"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0

test_result() {
    local name="$1"
    local expected="$2"
    local actual="$3"

    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}PASS${NC}: $name"
        ((PASS_COUNT++))
    else
        echo -e "${RED}FAIL${NC}: $name (expected=$expected, actual=$actual)"
        ((FAIL_COUNT++))
    fi
}

cleanup() {
    rm -rf "$TEST_PROJECT"
}

setup_test_project() {
    cleanup
    mkdir -p "$TEST_PROJECT/rules"
    mkdir -p "$TEST_PROJECT/specs/main/requirements"
    echo "# Test Rule" > "$TEST_PROJECT/rules/test.md"
    echo "# Test Spec" > "$TEST_PROJECT/specs/main/requirements/test.md"
}

echo "=================================================="
echo "Setup Upgrade Test Suite"
echo "=================================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Test project: $TEST_PROJECT"
echo ""

# ==================================================
echo "=================================================="
echo "Test 1: Clean install (no existing .claude)"
echo "=================================================="

setup_test_project

# Run setup with defaults
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Verify structure
test_result "agents/ created" "0" "$([[ -d "$TEST_PROJECT/.claude/agents" ]] && echo 0 || echo 1)"
test_result "skills/doc-advisor/SKILL.md created" "0" "$([[ -f "$TEST_PROJECT/.claude/skills/doc-advisor/SKILL.md" ]] && echo 0 || echo 1)"
test_result "doc-advisor/config.yaml created" "0" "$([[ -f "$TEST_PROJECT/.claude/doc-advisor/config.yaml" ]] && echo 0 || echo 1)"
test_result "doc-advisor/docs/ created" "0" "$([[ -d "$TEST_PROJECT/.claude/doc-advisor/docs" ]] && echo 0 || echo 1)"
test_result "doc-advisor/scripts/ created" "0" "$([[ -d "$TEST_PROJECT/.claude/doc-advisor/scripts" ]] && echo 0 || echo 1)"
test_result "doc-advisor/toc/rules/ created" "0" "$([[ -d "$TEST_PROJECT/.claude/doc-advisor/toc/rules" ]] && echo 0 || echo 1)"
test_result "doc-advisor/toc/specs/ created" "0" "$([[ -d "$TEST_PROJECT/.claude/doc-advisor/toc/specs" ]] && echo 0 || echo 1)"
test_result "No commands/ (legacy)" "1" "$([[ -d "$TEST_PROJECT/.claude/commands" ]] && echo 0 || echo 1)"
echo ""

# ==================================================
echo "=================================================="
echo "Test 2: Legacy commands/ auto-deleted (file-specific)"
echo "=================================================="

setup_test_project

# Create legacy structure
mkdir -p "$TEST_PROJECT/.claude/commands"
echo "# Legacy command" > "$TEST_PROJECT/.claude/commands/create-rules_toc.md"
echo "# Legacy command" > "$TEST_PROJECT/.claude/commands/create-specs_toc.md"
echo "# User custom command" > "$TEST_PROJECT/.claude/commands/my-custom-command.md"

# Run setup - legacy files are auto-deleted (no user confirmation)
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Verify: doc-advisor commands deleted, user custom preserved
test_result "Legacy create-rules_toc.md deleted" "1" "$([[ -f "$TEST_PROJECT/.claude/commands/create-rules_toc.md" ]] && echo 0 || echo 1)"
test_result "Legacy create-specs_toc.md deleted" "1" "$([[ -f "$TEST_PROJECT/.claude/commands/create-specs_toc.md" ]] && echo 0 || echo 1)"
test_result "User custom command preserved" "0" "$([[ -f "$TEST_PROJECT/.claude/commands/my-custom-command.md" ]] && echo 0 || echo 1)"
echo ""

# ==================================================
echo "=================================================="
echo "Test 3: v3.0 structure verification"
echo "=================================================="

setup_test_project

# Run setup
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Verify new structure
test_result "config.yaml in doc-advisor/" "0" "$([[ -f "$TEST_PROJECT/.claude/doc-advisor/config.yaml" ]] && echo 0 || echo 1)"
test_result "docs/ in doc-advisor/" "0" "$([[ -d "$TEST_PROJECT/.claude/doc-advisor/docs" ]] && echo 0 || echo 1)"
test_result "scripts/ in doc-advisor/" "0" "$([[ -d "$TEST_PROJECT/.claude/doc-advisor/scripts" ]] && echo 0 || echo 1)"
test_result "toc/rules/ in doc-advisor/" "0" "$([[ -d "$TEST_PROJECT/.claude/doc-advisor/toc/rules" ]] && echo 0 || echo 1)"
test_result "toc/specs/ in doc-advisor/" "0" "$([[ -d "$TEST_PROJECT/.claude/doc-advisor/toc/specs" ]] && echo 0 || echo 1)"
test_result "Only SKILL.md in skills/doc-advisor/" "0" "$([[ -f "$TEST_PROJECT/.claude/skills/doc-advisor/SKILL.md" ]] && echo 0 || echo 1)"
test_result "No config in skills/doc-advisor/" "1" "$([[ -f "$TEST_PROJECT/.claude/skills/doc-advisor/config.yaml" ]] && echo 0 || echo 1)"
echo ""

# ==================================================
echo "=================================================="
echo "Test 4: config.yaml skip (preserve existing)"
echo "=================================================="

setup_test_project

# First install
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Add custom exclude to config
echo "      - my_custom_exclude" >> "$TEST_PROJECT/.claude/doc-advisor/config.yaml"
CUSTOM_LINE=$(grep -c "my_custom_exclude" "$TEST_PROJECT/.claude/doc-advisor/config.yaml" | tr -d '[:space:]')

# Run setup again with 's' to skip config
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus\ns" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Verify custom line is preserved
CUSTOM_LINE_AFTER=$(grep -c "my_custom_exclude" "$TEST_PROJECT/.claude/doc-advisor/config.yaml" 2>/dev/null | tr -d '[:space:]' || echo 0)
test_result "Custom config preserved (skip)" "$CUSTOM_LINE" "$CUSTOM_LINE_AFTER"
echo ""

# ==================================================
echo "=================================================="
echo "Test 5: config.yaml overwrite with backup"
echo "=================================================="

setup_test_project

# First install
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Add custom exclude to config
echo "      - my_custom_exclude" >> "$TEST_PROJECT/.claude/doc-advisor/config.yaml"

# Run setup again with 'o' to overwrite
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus\no" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Verify backup exists and custom line is gone from main config
test_result "Backup created" "0" "$([[ -f "$TEST_PROJECT/.claude/doc-advisor/config.yaml.bak" ]] && echo 0 || echo 1)"
CUSTOM_IN_BACKUP=$(grep -c "my_custom_exclude" "$TEST_PROJECT/.claude/doc-advisor/config.yaml.bak" 2>/dev/null | tr -d '[:space:]' || echo 0)
test_result "Custom in backup" "1" "$CUSTOM_IN_BACKUP"
CUSTOM_IN_NEW=$(grep -c "my_custom_exclude" "$TEST_PROJECT/.claude/doc-advisor/config.yaml" 2>/dev/null | tr -d '[:space:]' || echo 0)
test_result "Custom NOT in new config" "0" "$CUSTOM_IN_NEW"
echo ""

# ==================================================
echo "=================================================="
echo "Test 6: skills/doc-advisor/ contains only SKILL.md (clean install)"
echo "=================================================="

setup_test_project

# First install
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Create fake old files that shouldn't exist in new version
mkdir -p "$TEST_PROJECT/.claude/skills/doc-advisor/scripts"
mkdir -p "$TEST_PROJECT/.claude/skills/doc-advisor/docs"
echo "# Old script" > "$TEST_PROJECT/.claude/skills/doc-advisor/scripts/old_obsolete_script.py"
echo "# Old doc" > "$TEST_PROJECT/.claude/skills/doc-advisor/docs/old_obsolete_doc.md"

# Run setup again with 'o' to overwrite config
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus\no" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Verify old files are gone (skills/doc-advisor/ is clean install - only SKILL.md)
test_result "Old script removed" "1" "$([[ -f "$TEST_PROJECT/.claude/skills/doc-advisor/scripts/old_obsolete_script.py" ]] && echo 0 || echo 1)"
test_result "Old doc removed" "1" "$([[ -f "$TEST_PROJECT/.claude/skills/doc-advisor/docs/old_obsolete_doc.md" ]] && echo 0 || echo 1)"
test_result "No scripts/ in skills/doc-advisor/" "1" "$([[ -d "$TEST_PROJECT/.claude/skills/doc-advisor/scripts" ]] && echo 0 || echo 1)"
test_result "No docs/ in skills/doc-advisor/" "1" "$([[ -d "$TEST_PROJECT/.claude/skills/doc-advisor/docs" ]] && echo 0 || echo 1)"
test_result "Only SKILL.md exists" "0" "$([[ -f "$TEST_PROJECT/.claude/skills/doc-advisor/SKILL.md" ]] && echo 0 || echo 1)"
echo ""

# ==================================================
echo "=================================================="
echo "Test 7: agents/ custom agent preserved"
echo "=================================================="

setup_test_project

# First install
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Add custom agent
echo "# My custom agent" > "$TEST_PROJECT/.claude/agents/my-custom-agent.md"

# Run setup again
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus\ns" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Verify: custom agent preserved, managed agents still exist
test_result "Custom agent preserved" "0" "$([[ -f "$TEST_PROJECT/.claude/agents/my-custom-agent.md" ]] && echo 0 || echo 1)"
test_result "Managed agent exists" "0" "$([[ -f "$TEST_PROJECT/.claude/agents/rules-advisor.md" ]] && echo 0 || echo 1)"
echo ""

# ==================================================
echo "=================================================="
echo "Test 8: Repeated setup preserves toc/ directory structure"
echo "=================================================="

setup_test_project

# First install
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Create fake ToC files (simulating generated output)
echo "# Generated ToC" > "$TEST_PROJECT/.claude/doc-advisor/toc/rules/rules_toc.yaml"
echo "# Generated ToC" > "$TEST_PROJECT/.claude/doc-advisor/toc/specs/specs_toc.yaml"

# Run setup again with 's' to skip config
echo -e "rules\nspecs\nrequirements\ndesign\nplan\nopus\ns" | "$PROJECT_ROOT/setup.sh" "$TEST_PROJECT" > /dev/null 2>&1

# Verify: toc files are preserved
test_result "rules_toc.yaml preserved" "0" "$([[ -f "$TEST_PROJECT/.claude/doc-advisor/toc/rules/rules_toc.yaml" ]] && echo 0 || echo 1)"
test_result "specs_toc.yaml preserved" "0" "$([[ -f "$TEST_PROJECT/.claude/doc-advisor/toc/specs/specs_toc.yaml" ]] && echo 0 || echo 1)"
echo ""

# ==================================================
# Cleanup
cleanup

echo "=================================================="
echo "Summary"
echo "=================================================="
echo ""
echo -e "Passed: ${GREEN}$PASS_COUNT${NC}"
echo -e "Failed: ${RED}$FAIL_COUNT${NC}"
echo ""

if [[ $FAIL_COUNT -eq 0 ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi

#!/bin/bash
# Doc Advisor Plugin Setup Script
#
# Usage:
#   ./setup.sh [--rules-dir <path>] [--specs-dir <path>]
#
# Options:
#   --rules-dir <path>  Development documentation directory (default: rules/)
#   --specs-dir <path>  Requirements/design documents directory (default: specs/)
#   -h, --help          Show help
#
# Examples:
#   ./setup.sh                                    # Default settings
#   ./setup.sh --rules-dir docs/rules/            # Custom rules only
#   ./setup.sh --rules-dir docs/ --specs-dir specifications/

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Default values
RULES_DIR="rules/"
SPECS_DIR="specs/"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --rules-dir)
            RULES_DIR="$2"
            shift 2
            ;;
        --specs-dir)
            SPECS_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Doc Advisor Plugin Setup Script"
            echo ""
            echo "Usage:"
            echo "  ./setup.sh [--rules-dir <path>] [--specs-dir <path>]"
            echo ""
            echo "Options:"
            echo "  --rules-dir <path>  Development documentation directory (default: rules/)"
            echo "  --specs-dir <path>  Requirements/design documents directory (default: specs/)"
            echo "  -h, --help          Show help"
            echo ""
            echo "Examples:"
            echo "  ./setup.sh                                    # Default settings"
            echo "  ./setup.sh --rules-dir docs/rules/            # Custom rules only"
            echo "  ./setup.sh --rules-dir docs/ --specs-dir specifications/"
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1"
            echo "Run ./setup.sh --help for usage information"
            exit 1
            ;;
    esac
done

# Ensure trailing slash
[[ "${RULES_DIR}" != */ ]] && RULES_DIR="${RULES_DIR}/"
[[ "${SPECS_DIR}" != */ ]] && SPECS_DIR="${SPECS_DIR}/"

echo "=========================================="
echo "Doc Advisor Plugin Setup"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  RULES_DIR: ${RULES_DIR}"
echo "  SPECS_DIR: ${SPECS_DIR}"
echo ""

# Check templates directory exists
if [[ ! -d "${SCRIPT_DIR}/templates" ]]; then
    echo "Error: templates/ directory not found"
    exit 1
fi

# Placeholder replacement function
replace_placeholders() {
    local file="$1"
    # Replace placeholders with sed (works on both macOS and Linux)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|{{RULES_DIR}}|${RULES_DIR}|g" "$file"
        sed -i '' "s|{{SPECS_DIR}}|${SPECS_DIR}|g" "$file"
    else
        sed -i "s|{{RULES_DIR}}|${RULES_DIR}|g" "$file"
        sed -i "s|{{SPECS_DIR}}|${SPECS_DIR}|g" "$file"
    fi
}

# Generate agents/ directory
echo "📁 Generating agents/..."
mkdir -p "${SCRIPT_DIR}/agents"
for template in "${SCRIPT_DIR}/templates/agents/"*.md; do
    if [[ -f "$template" ]]; then
        filename=$(basename "$template")
        target="${SCRIPT_DIR}/agents/${filename}"
        cp "$template" "$target"
        replace_placeholders "$target"
        echo "   ✓ ${filename}"
    fi
done

# Generate commands/ directory
echo "📁 Generating commands/..."
mkdir -p "${SCRIPT_DIR}/commands"
for template in "${SCRIPT_DIR}/templates/commands/"*.md; do
    if [[ -f "$template" ]]; then
        filename=$(basename "$template")
        target="${SCRIPT_DIR}/commands/${filename}"
        cp "$template" "$target"
        replace_placeholders "$target"
        echo "   ✓ ${filename}"
    fi
done

# Generate skills/toc-common/config.yaml
echo "📁 Generating skills/toc-common/config.yaml..."
mkdir -p "${SCRIPT_DIR}/skills/toc-common"
if [[ -f "${SCRIPT_DIR}/templates/skills/toc-common/config.yaml" ]]; then
    cp "${SCRIPT_DIR}/templates/skills/toc-common/config.yaml" "${SCRIPT_DIR}/skills/toc-common/config.yaml"
    replace_placeholders "${SCRIPT_DIR}/skills/toc-common/config.yaml"
    echo "   ✓ config.yaml"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Verify ${RULES_DIR} and ${SPECS_DIR} directories exist in your project"
echo "  2. Run /doc-advisor:create-rules_toc --full for initial ToC generation"
echo "  3. Run /doc-advisor:create-specs_toc --full for initial ToC generation"
echo ""

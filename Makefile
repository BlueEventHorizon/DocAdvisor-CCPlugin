# Doc Advisor Makefile (v3.3)
#
# Usage:
#   make help               # Show help
#   make setup              # Setup (interactive mode)
#   make setup TARGET=/path # Setup target project
#
# Note: This tool copies templates to target project.
# Config is stored at: TARGET/.claude/doc-advisor/config.yaml

.PHONY: help setup add-exclude

# Default target
.DEFAULT_GOAL := help

help:
	@echo "Doc Advisor (v3.3)"
	@echo ""
	@echo "Usage:"
	@echo "  make help                    Show this help message"
	@echo "  make setup                   Setup (interactive mode)"
	@echo "  make setup TARGET=/path      Setup target project"
	@echo "  make add-exclude TARGET=/path  Add exclude patterns to config"
	@echo ""
	@echo "Examples:"
	@echo "  make setup"
	@echo "  make setup TARGET=~/projects/my-app"
	@echo ""
	@echo "After setup, start Claude Code with:"
	@echo "  cd TARGET && claude"
	@echo ""
	@echo "Files created at:"
	@echo "  TARGET/.claude/commands/        Command files"
	@echo "  TARGET/.claude/agents/          Agent definitions"
	@echo "  TARGET/.claude/skills/          Skill modules"
	@echo "  TARGET/.claude/doc-advisor/     Configuration"

setup:
	@./setup.sh $(TARGET)

add-exclude:
	@./add-exclude.sh $(TARGET)

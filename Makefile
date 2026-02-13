# Upkeep Makefile
# Unified command interface for all development tasks
#
# Usage:
#   make help      - Show available commands
#   make test      - Run all tests
#   make lint      - Run all linters
#   make fix       - Auto-fix formatting issues
#   make verify    - Full verification (lint + test)
#   make ci        - Simulate CI pipeline locally

.PHONY: help setup test lint fix format verify ci clean build dev
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# Detect if we're in a virtual environment
VENV_ACTIVE := $(shell python -c 'import sys; print(1 if sys.prefix != sys.base_prefix else 0)' 2>/dev/null || echo 0)

# ============================================================================
# Help
# ============================================================================
help:
	@echo ""
	@echo "$(BLUE)Upkeep Development Commands$(NC)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make setup       Install all dependencies (Python + Node)"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test        Run all tests (Python + TypeScript + Bash)"
	@echo "  make test-py     Run Python tests only"
	@echo "  make test-ts     Run TypeScript tests only"
	@echo "  make test-bash   Run Bash tests only"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make lint        Run all linters (no auto-fix)"
	@echo "  make fix         Auto-fix formatting issues"
	@echo "  make format      Alias for fix"
	@echo "  make typecheck   Run type checkers (Python + TypeScript)"
	@echo ""
	@echo "$(GREEN)Verification:$(NC)"
	@echo "  make verify      Full verification (lint + test)"
	@echo "  make ci          Simulate full CI pipeline locally"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev         Start development server with watch"
	@echo "  make build       Build TypeScript"
	@echo "  make clean       Remove build artifacts"
	@echo ""

# ============================================================================
# Setup
# ============================================================================
setup: setup-py setup-node
	@echo "$(GREEN)✓ Setup complete$(NC)"

setup-py:
	@echo "$(BLUE)▶ Setting up Python environment...$(NC)"
	@if [ ! -d .venv ]; then uv venv .venv; fi
	@. .venv/bin/activate && uv pip install -e ".[dev]"
	@echo "$(GREEN)✓ Python setup complete$(NC)"

setup-node:
	@echo "$(BLUE)▶ Installing Node dependencies...$(NC)"
	@npm ci
	@echo "$(GREEN)✓ Node setup complete$(NC)"

# ============================================================================
# Testing
# ============================================================================
test: test-py test-ts test-bash
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(GREEN)✓ All tests passed$(NC)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"

test-py:
	@echo ""
	@echo "$(BLUE)▶ Running Python tests...$(NC)"
	@. .venv/bin/activate && pytest tests/python -v --tb=short -q

test-ts:
	@echo ""
	@echo "$(BLUE)▶ Running TypeScript tests...$(NC)"
	@npm run test:run

test-bash:
	@echo ""
	@echo "$(BLUE)▶ Running Bash tests...$(NC)"
	@chmod +x tests/run_all_tests.sh
	@./tests/run_all_tests.sh

# ============================================================================
# Linting
# ============================================================================
lint: lint-py lint-ts lint-bash
	@echo ""
	@echo "$(GREEN)✓ All linters passed$(NC)"

lint-py:
	@echo ""
	@echo "$(BLUE)▶ Linting Python...$(NC)"
	@. .venv/bin/activate && ruff check src/ tests/
	@. .venv/bin/activate && ruff format --check src/ tests/

lint-ts:
	@echo ""
	@echo "$(BLUE)▶ Type-checking TypeScript...$(NC)"
	@npm run type-check

lint-bash:
	@echo ""
	@echo "$(BLUE)▶ Checking Bash scripts with ShellCheck...$(NC)"
	@shellcheck -x upkeep.sh 2>/dev/null || echo "$(YELLOW)⚠ ShellCheck warnings in upkeep.sh$(NC)"

# ============================================================================
# Formatting / Auto-fix
# ============================================================================
fix: fix-py fix-ts
	@echo ""
	@echo "$(GREEN)✓ Auto-fix complete$(NC)"

format: fix

fix-py:
	@echo ""
	@echo "$(BLUE)▶ Formatting Python...$(NC)"
	@. .venv/bin/activate && ruff check --fix src/ tests/ || true
	@. .venv/bin/activate && ruff format src/ tests/

fix-ts:
	@echo ""
	@echo "$(BLUE)▶ Formatting TypeScript (if prettier configured)...$(NC)"
	@if [ -f .prettierrc ] || [ -f .prettierrc.json ]; then npx prettier --write "src/**/*.ts" "types/**/*.ts"; else echo "No prettier config, skipping"; fi

# ============================================================================
# Type Checking
# ============================================================================
typecheck: typecheck-py typecheck-ts
	@echo ""
	@echo "$(GREEN)✓ Type checks passed$(NC)"

typecheck-py:
	@echo ""
	@echo "$(BLUE)▶ Type-checking Python...$(NC)"
	@. .venv/bin/activate && mypy src/upkeep --ignore-missing-imports || true

typecheck-ts:
	@echo ""
	@echo "$(BLUE)▶ Type-checking TypeScript...$(NC)"
	@npm run type-check

# ============================================================================
# Verification
# ============================================================================
verify: lint test
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(GREEN)✓ VERIFICATION COMPLETE$(NC)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"

ci: clean setup lint typecheck test
	@echo ""
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(GREEN)✓ CI SIMULATION COMPLETE$(NC)"
	@echo "$(GREEN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"

# ============================================================================
# Build
# ============================================================================
build: build-ts
	@echo "$(GREEN)✓ Build complete$(NC)"

build-ts:
	@echo ""
	@echo "$(BLUE)▶ Building TypeScript...$(NC)"
	@npm run build:web

# ============================================================================
# Development
# ============================================================================
dev:
	@echo "$(BLUE)▶ Starting development server...$(NC)"
	@./run-web.sh &
	@npm run watch:web

# ============================================================================
# Clean
# ============================================================================
clean:
	@echo "$(BLUE)▶ Cleaning build artifacts...$(NC)"
	@rm -rf .pytest_cache
	@rm -rf .ruff_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@rm -rf coverage.xml
	@rm -rf src/upkeep/web/static/app.js src/upkeep/web/static/app.js.map
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Clean complete$(NC)"

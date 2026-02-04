#!/usr/bin/env bash
# TypeScript type checking for JavaScript and TypeScript files
# - JavaScript: Uses JSDoc annotations + TypeScript's --checkJs mode
# - TypeScript: Full type checking with strict mode
# No build step required - this is type checking only

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}ℹ️  $*${NC}"
}

success() {
    echo -e "${GREEN}✅ $*${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $*${NC}"
}

error() {
    echo -e "${RED}❌ $*${NC}"
}

# Check if tsc is installed
if ! command -v tsc &> /dev/null; then
    warning "TypeScript compiler (tsc) not found. Installing..."
    npm install -g typescript
fi

info "Running TypeScript type checking..."

# Count TypeScript files
TS_COUNT=$(find src/upkeep/web/static/ts -name "*.ts" 2>/dev/null | wc -l | tr -d ' ')

if [ "$TS_COUNT" -gt 0 ]; then
    info "Checking $TS_COUNT TypeScript files..."
else
    info "Checking JavaScript files with JSDoc annotations..."
fi

# Run TypeScript compiler in check-only mode
if tsc --noEmit; then
    success "Type checking passed! No type errors found."
    if [ "$TS_COUNT" -gt 0 ]; then
        success "All TypeScript modules are type-safe."
    else
        success "Your JavaScript code has proper type safety."
    fi
    exit 0
else
    error "Type checking failed. See errors above."
    echo ""
    info "How to fix type errors:"
    if [ "$TS_COUNT" -gt 0 ]; then
        echo "  1. Review the errors in your TypeScript files"
        echo "  2. Fix type mismatches, null checks, and missing properties"
        echo "  3. Run 'npm run type-check' to re-check"
        echo ""
        info "Common fixes:"
        echo "  - Add null checks: if (element) { ... }"
        echo "  - Use non-null assertion: value!"
        echo "  - Add optional chaining: object?.property"
        echo "  - Update type definitions in types/api.d.ts"
    else
        echo "  1. Add JSDoc type annotations to your JavaScript"
        echo "  2. Fix type mismatches highlighted above"
        echo "  3. Run 'tsc --noEmit' to re-check"
        echo ""
        info "Example JSDoc annotations:"
        echo "  /** @type {MaintenanceOperation} */"
        echo "  const operation = data;"
        echo ""
        echo "  /**"
        echo "   * @param {string} url - API endpoint"
        echo "   * @param {MaintenanceOperation} operation - Operation data"
        echo "   * @returns {Promise<OperationsListResponse>}"
        echo "   */"
        echo "  async function fetchOperation(url, operation) {"
        echo "    // ..."
        echo "  }"
    fi
    exit 1
fi

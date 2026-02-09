#!/bin/bash
# Pre-commit checks: formatting, linting, type checking, and tests
# Run this before committing changes

set -e

echo "========================================"
echo "Running pre-commit checks..."
echo "========================================"

echo ""
echo "1/5 Running code formatting (ruff format)..."
echo "----------------------------------------"
uv run ruff format src/ --check || {
    echo ""
    echo "Formatting issues found. Run 'uv run ruff format src/' to fix."
    exit 1
}

echo ""
echo "2/5 Running linting (ruff check)..."
echo "----------------------------------------"
uv run ruff check src/

echo ""
echo "3/5 Running type checking (mypy)..."
echo "----------------------------------------"
uv run mypy src/legacylipi --ignore-missing-imports

echo ""
echo "4/5 Running Python tests (pytest)..."
echo "----------------------------------------"
uv run pytest tests/ -v --tb=short

echo ""
echo "5/5 Running frontend checks..."
echo "----------------------------------------"
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    cd frontend
    npx tsc --noEmit
    echo "TypeScript: OK"
    cd ..
else
    echo "Frontend not found, skipping."
fi

echo ""
echo "========================================"
echo "All checks passed! Ready to commit."
echo "========================================"

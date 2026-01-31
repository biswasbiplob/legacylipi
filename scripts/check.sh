#!/bin/bash
# Pre-commit checks: linting, type checking, and tests
# Run this before committing changes

set -e

echo "========================================"
echo "Running pre-commit checks..."
echo "========================================"

echo ""
echo "1/3 Running linting (ruff)..."
echo "----------------------------------------"
uv run ruff check src/

echo ""
echo "2/3 Running type checking (mypy)..."
echo "----------------------------------------"
uv run mypy src/legacylipi --ignore-missing-imports

echo ""
echo "3/3 Running tests (pytest)..."
echo "----------------------------------------"
uv run pytest tests/ -v --tb=short

echo ""
echo "========================================"
echo "All checks passed! Ready to commit."
echo "========================================"

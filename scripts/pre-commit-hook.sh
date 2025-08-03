#!/bin/bash
set -e

echo "🔧 Running pre-commit checks..."

# Step 1: Run linting (includes formatting)
echo "🔍 Running linting checks..."
make lint

# Step 2: Stage any formatting changes
echo "📦 Staging formatting changes..."
git add -A

# Step 3: Run tests
echo "🧪 Running tests..."
make test

echo "✅ All checks passed!"
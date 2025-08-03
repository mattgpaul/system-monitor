#!/bin/bash
set -e

echo "🔧 Running pre-commit checks..."

# Step 1: Format code
echo "📝 Formatting code..."
./venv/bin/python -m black app/ tests/
./venv/bin/python -m isort app/ tests/

# Step 2: Stage any formatting changes
echo "📦 Staging formatting changes..."
git add -A

# Step 3: Run linting (should pass now)
echo "🔍 Running linting checks..."
./venv/bin/python -m flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503
./venv/bin/python -m mypy app/

# Step 4: Run tests
echo "🧪 Running tests..."
./venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

echo "✅ All checks passed!"
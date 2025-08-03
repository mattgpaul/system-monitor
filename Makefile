# System Monitor - Build automation
# Usage: make <target>

.PHONY: help install test clean format lint pytest
.DEFAULT_GOAL := help

help:  ## Show available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv:  ## Create virtual environment if it doesn't exist
	test -d venv || python3 -m venv venv

dev: venv  ## Install dependencies and setup development environment
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -e .[dev,agent,container]

test: venv  ## Run all tests with coverage
	./venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

pytest: venv  ## Run pytest with custom args
	./venv/bin/python -m pytest tests/ $(filter-out $@ --,$(MAKECMDGOALS))

# Prevent Make from treating pytest args as targets  
%:
	@:

clean:  ## Clean up generated files and artifacts
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

format: venv	## Auto-fix code formatting and imports
	./venv/bin/python -m black app/ tests/
	./venv/bin/python -m isort app/ tests/

lint: format	## Run formatting then check for code issues
	./venv/bin/python -m flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	./venv/bin/python -m mypy app/

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
	./venv/bin/pip install -e .[dev,agent,server]
	@chmod +x scripts/start-dev.sh
	@./scripts/start-dev.sh

dev-agent: venv  ## Start only the agent in development mode
	ENV=dev ./venv/bin/python app/agent/main.py --server

dev-server: venv  ## Start only the Django server in development mode
	ENV=dev ./venv/bin/python app/server/manage.py runserver; \

dev-test-poll: venv  ## Test server polling task against running agent
	@chmod +x scripts/test-poll.py
	@ENV=dev ./venv/bin/python scripts/test-poll.py

dev-test: venv  ## Run tests in development environment
	ENV=dev ./venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Production targets
prod-agent: venv  ## Start agent in production mode
	ENV=prod ./venv/bin/python app/agent/main.py --server

prod-server: venv  ## Start server in production mode
	@if [ -f "prod.env" ]; then \
		source prod.env && ENV=prod ./venv/bin/python app/server/manage.py runserver $$SERVER_HOST:$$SERVER_PORT; \
	else \
		ENV=prod ./venv/bin/python app/server/manage.py runserver; \
	fi


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

lint-fix: venv  ## Auto-fix linting issues where possible
	./venv/bin/python -m autoflake --remove-all-unused-imports --remove-unused-variables --recursive --in-place app/ tests/
	./venv/bin/python -m black app/ tests/
	./venv/bin/python -m isort app/ tests/
	@echo "Auto-fixes applied! Running final check..."
	./venv/bin/python -m flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503,E402

lint-all: lint lint-types  ## Run all linting including type checking
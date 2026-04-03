# NesterVoiceAI Makefile
# Development and deployment commands

.PHONY: help install dev test lint format run docker-build docker-up docker-down clean

# Default target
help:
	@echo "NesterVoiceAI - Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install production dependencies"
	@echo "  make dev         - Install development dependencies"
	@echo "  make run         - Run the application locally"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run all tests"
	@echo "  make test-unit   - Run unit tests only"
	@echo "  make test-cov    - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        - Run linter (ruff)"
	@echo "  make format      - Format code (black)"
	@echo "  make type-check  - Run type checker (mypy)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start containers"
	@echo "  make docker-down  - Stop containers"
	@echo "  make docker-logs  - View container logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       - Remove cache and build files"

# Installation
install:
	pip install -r requirements.txt

dev:
	pip install -e ".[dev]"

# Running
run:
	python -m app.main

run-uvicorn:
	uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Code Quality
lint:
	ruff check app/ tests/

lint-fix:
	ruff check --fix app/ tests/

format:
	black app/ tests/

format-check:
	black --check app/ tests/

type-check:
	mypy app/

# Docker
docker-build:
	docker-compose -f deployment/docker/docker-compose.yml build

docker-up:
	docker-compose -f deployment/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f deployment/docker/docker-compose.yml down

docker-logs:
	docker-compose -f deployment/docker/docker-compose.yml logs -f

docker-https-up:
	docker-compose -f deployment/docker/docker-compose.https.yml up -d

docker-https-down:
	docker-compose -f deployment/docker/docker-compose.https.yml down

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ build/ dist/ 2>/dev/null || true

# Pre-commit
pre-commit:
	pre-commit run --all-files

# Quick check before commit
check: format lint type-check test
	@echo "All checks passed!"

.DEFAULT_GOAL := help

WEB_DIR := web
IMAGE_API := fastapi-datallmreact-api
IMAGE_WEB := fastapi-datallmreact-web
NEXT_PUBLIC_WEBSITE_URL ?= http://localhost:3000
NEXT_PUBLIC_API_URL ?= http://localhost:8000

.PHONY: help install install-backend install-frontend \
	lint lint-backend lint-frontend format typecheck-frontend \
	test test-backend migrate migration seed \
	build build-backend build-frontend \
	up prod-up down logs ci clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: install-backend install-frontend ## Install backend + frontend dependencies

install-backend: ## Install backend dependencies (uv)
	uv sync

install-frontend: ## Install frontend dependencies (npm)
	npm ci --prefix $(WEB_DIR)

lint: lint-backend lint-frontend ## Lint backend + frontend

lint-backend: ## Lint backend with ruff (check + format check)
	uv run ruff check .
	uv run ruff format --check .

lint-frontend: ## Lint frontend with next lint
	npm run lint --prefix $(WEB_DIR)

format: ## Auto-format backend code with ruff
	uv run ruff format .

typecheck-frontend: ## Typecheck frontend with tsc
	cd $(WEB_DIR) && npx tsc --noEmit

test: test-backend ## Run tests (frontend has no test framework configured yet)

test-backend: migrate ## Run backend tests with coverage
	uv run pytest --cov=app --cov-report=term-missing

migrate: ## Apply database migrations
	uv run alembic upgrade head

migration: ## Create a new migration (usage: make migration name="add x")
	uv run alembic revision --autogenerate -m "$(name)"

seed: ## Seed the database from source/ (usage: make seed force=1 to wipe and reseed)
	uv run python scripts/seed_from_source.py $(if $(force),--force,)

build: build-backend build-frontend ## Build backend + frontend Docker images

build-backend: ## Build backend Docker image
	docker build -t $(IMAGE_API) .

build-frontend: ## Build frontend Docker image
	docker build -t $(IMAGE_WEB) $(WEB_DIR) \
		--build-arg NEXT_PUBLIC_WEBSITE_URL=$(NEXT_PUBLIC_WEBSITE_URL) \
		--build-arg NEXT_PUBLIC_API_URL=$(NEXT_PUBLIC_API_URL)

up: ## Start local dev stack with live sync (docker compose watch)
	docker compose watch

prod-up: ## Start the stack the same way prod does (build + detached, no watch)
	docker compose up --build -d

down: ## Stop the stack
	docker compose down

logs: ## Tail logs from the stack
	docker compose logs -f

ci: install lint typecheck-frontend test build ## Run the full check suite locally, same as CI

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache .coverage $(WEB_DIR)/.next
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +

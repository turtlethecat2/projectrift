# Project Rift - Makefile
# Common commands for development and operations

.PHONY: help install start stop test format db-migrate db-seed db-reset dbt-run dbt-test dbt-docs logs-api logs-hud clean

# Default target
.DEFAULT_GOAL := help

# Load environment variables
include .env
export

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Project Rift - Available Commands$(NC)"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(BLUE)Installing development tools...$(NC)"
	pip install -r requirements-dev.txt
	@echo "$(GREEN)✓ Development tools installed$(NC)"

start: ## Start API and HUD (in background)
	@echo "$(BLUE)Starting Project Rift...$(NC)"
	@nohup uvicorn api.main:app --reload --host $(API_HOST) --port $(API_PORT) > logs/api.log 2>&1 &
	@echo "API started on http://$(API_HOST):$(API_PORT)"
	@sleep 2
	@nohup streamlit run app/main_hud.py > logs/hud.log 2>&1 &
	@echo "HUD started on http://localhost:8501"
	@echo "$(GREEN)✓ Project Rift is running$(NC)"

start-api: ## Start only the API
	@echo "$(BLUE)Starting API...$(NC)"
	uvicorn api.main:app --reload --host $(API_HOST) --port $(API_PORT)

start-hud: ## Start only the HUD
	@echo "$(BLUE)Starting HUD...$(NC)"
	streamlit run app/main_hud.py

stop: ## Stop API and HUD
	@echo "$(BLUE)Stopping Project Rift...$(NC)"
	@pkill -f "uvicorn api.main:app" || true
	@pkill -f "streamlit run app/main_hud.py" || true
	@echo "$(GREEN)✓ Project Rift stopped$(NC)"

restart: stop start ## Restart API and HUD

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v --cov=api --cov=app

test-api: ## Run API tests only
	@echo "$(BLUE)Running API tests...$(NC)"
	pytest tests/test_api.py -v

test-db: ## Run database tests only
	@echo "$(BLUE)Running database tests...$(NC)"
	pytest tests/test_database.py -v

test-webhooks: ## Run webhook integration tests only
	@echo "$(BLUE)Running webhook tests...$(NC)"
	pytest tests/test_webhooks.py -v

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black api/ app/ tests/ database/ scripts/
	isort api/ app/ tests/ database/ scripts/
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Run linting checks
	@echo "$(BLUE)Running linters...$(NC)"
	flake8 api/ app/ tests/ database/ scripts/
	mypy api/ app/ database/
	@echo "$(GREEN)✓ Linting complete$(NC)"

db-migrate: ## Initialize database with schema
	@echo "$(BLUE)Initializing database...$(NC)"
	psql $(DATABASE_URL) < database/init_db.sql
	@echo "$(GREEN)✓ Database initialized$(NC)"

db-seed: ## Seed database with test data
	@echo "$(BLUE)Seeding database...$(NC)"
	python scripts/seed_data.py
	@echo "$(GREEN)✓ Database seeded$(NC)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		echo "$(BLUE)Resetting database...$(NC)"; \
		psql $(DATABASE_URL) -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; \
		$(MAKE) db-migrate; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
	fi

db-cleanup: ## Clean up old events (dry run)
	@echo "$(BLUE)Cleaning up old events (dry run)...$(NC)"
	python scripts/cleanup_old_events.py --dry-run

db-cleanup-live: ## Clean up old events (LIVE - deletes data)
	@echo "$(BLUE)Cleaning up old events...$(NC)"
	python scripts/cleanup_old_events.py

db-stats: ## Show database statistics
	@echo "$(BLUE)Database Statistics:$(NC)"
	python scripts/cleanup_old_events.py --stats

dbt-run: ## Run dbt models
	@echo "$(BLUE)Running dbt models...$(NC)"
	cd dbt_project && dbt run
	@echo "$(GREEN)✓ dbt models executed$(NC)"

dbt-test: ## Run dbt tests
	@echo "$(BLUE)Running dbt tests...$(NC)"
	cd dbt_project && dbt test
	@echo "$(GREEN)✓ dbt tests complete$(NC)"

dbt-docs: ## Generate and serve dbt documentation
	@echo "$(BLUE)Generating dbt documentation...$(NC)"
	cd dbt_project && dbt docs generate && dbt docs serve

dbt-full: ## Run dbt with tests and documentation
	@echo "$(BLUE)Running full dbt pipeline...$(NC)"
	./scripts/run_dbt.sh --docs

logs-api: ## Tail API logs
	@echo "$(BLUE)Tailing API logs...$(NC)"
	tail -f logs/api.log

logs-hud: ## Tail HUD logs
	@echo "$(BLUE)Tailing HUD logs...$(NC)"
	tail -f logs/hud.log

logs: ## Tail all logs
	@echo "$(BLUE)Tailing all logs...$(NC)"
	tail -f logs/*.log

clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/
	rm -rf dbt_project/target dbt_project/dbt_packages dbt_project/logs
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

health: ## Check API health
	@echo "$(BLUE)Checking API health...$(NC)"
	@curl -s http://$(API_HOST):$(API_PORT)/api/v1/health | python -m json.tool

stats: ## Get current stats from API
	@echo "$(BLUE)Fetching current stats...$(NC)"
	@curl -s http://$(API_HOST):$(API_PORT)/api/v1/stats/current | python -m json.tool

webhook-test: ## Send test webhook
	@echo "$(BLUE)Sending test webhook...$(NC)"
	@curl -X POST http://$(API_HOST):$(API_PORT)/api/v1/webhook/ingest \
		-H "Content-Type: application/json" \
		-H "X-RIFT-SECRET: $(WEBHOOK_SECRET)" \
		-d '{"source": "manual", "event_type": "call_dial", "metadata": {"test": true}}' | python -m json.tool

dev-setup: ## Complete development setup
	@echo "$(BLUE)Setting up Project Rift for development...$(NC)"
	$(MAKE) install
	@echo ""
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "1. Copy .env.example to .env and fill in your values"
	@echo "2. Run 'make db-migrate' to initialize the database"
	@echo "3. Run 'make db-seed' to add test data (optional)"
	@echo "4. Run 'make start' to start the application"
	@echo ""
	@echo "$(GREEN)✓ Development environment ready$(NC)"

.PHONY: all
all: format lint test ## Run format, lint, and test

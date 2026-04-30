# Project Rift — MVP Makefile (loads `.env` when present)

-include .env
export

.PHONY: help install install-dev start start-api start-hud stop test db-migrate db-seed clean health webhook-test dbt-run

.DEFAULT_GOAL := help

API_HOST ?= 0.0.0.0
API_PORT ?= 8000

help:
	@echo "Project Rift (MVP)"
	@echo ""
	@echo "  make install       pip install runtime deps"
	@echo "  make db-migrate    apply database/init_db.sql"
	@echo "  make start-api     FastAPI (foreground)"
	@echo "  make start-hud     Streamlit HUD (foreground)"
	@echo "  make start         API + HUD in background (logs in logs/)"
	@echo "  make stop          stop background API + HUD"
	@echo "  make health        curl GET /api/v1/health"
	@echo "  make webhook-test  POST sample event"
	@echo "  make dbt-run       run dbt models"
	@echo ""
	@echo "Docker: docker compose up -d postgres"

install:
	python -m pip install -r requirements.txt

install-dev: install
	python -m pip install -r requirements-dev.txt

start: logs-dir
	@echo "Starting API on http://$(API_HOST):$(API_PORT) ..."
	@nohup uvicorn api.main:app --reload --host $(API_HOST) --port $(API_PORT) > logs/api.log 2>&1 &
	@sleep 2
	@echo "Starting HUD on http://localhost:8501 ..."
	@PYTHONPATH=. nohup streamlit run app/main_hud.py --server.headless true > logs/hud.log 2>&1 &
	@echo "Done. Tail logs: make logs-api / make logs-hud"

logs-dir:
	@mkdir -p logs

start-api:
	PYTHONPATH=. uvicorn api.main:app --reload --host $(API_HOST) --port $(API_PORT)

start-hud:
	PYTHONPATH=. streamlit run app/main_hud.py

stop:
	-pkill -f "uvicorn api.main:app" || true
	-pkill -f "streamlit run app/main_hud.py" || true

db-migrate:
	psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 -f database/init_db.sql

db-seed:
	python scripts/seed_data.py --direct

test:
	pytest tests/ -q

health:
	@curl -s "http://127.0.0.1:$(API_PORT)/api/v1/health" | python -m json.tool

webhook-test:
	@curl -s -X POST "http://127.0.0.1:$(API_PORT)/api/v1/webhook/ingest" \
	  -H "Content-Type: application/json" \
	  -H "X-RIFT-SECRET: $(WEBHOOK_SECRET)" \
	  -d '{"source":"manual","event_type":"call_dial","metadata":{"note":"make webhook-test"}}' \
	  | python -m json.tool

dbt-run:
	cd dbt_project && DBT_PROFILES_DIR=. dbt run

dbt-debug:
	cd dbt_project && DBT_PROFILES_DIR=. dbt debug

logs-api:
	tail -f logs/api.log

logs-hud:
	tail -f logs/hud.log

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

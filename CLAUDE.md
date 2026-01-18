# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Project Rift is a League of Legends-inspired gamification engine for SDRs. It transforms sales activities into gaming metrics (XP, levels, gold, ranks).

**Stack:** Python 3.10+ | FastAPI | Streamlit | PostgreSQL | dbt

**Current State:** Fully functional. API on port 8000, HUD on port 8501.

## Commands

```bash
# Run
make start            # API + HUD in background
make start-api        # API only (foreground, hot reload)
make start-hud        # HUD only (foreground)
make stop             # Stop all

# Test
make test             # All tests with coverage
pytest tests/test_api.py::test_name -v  # Single test

# Code Quality (run before commits)
make format           # black + isort
make lint             # flake8 + mypy

# Database
make db-migrate       # Init schema
make db-seed          # Seed test data
```

## Debugging

```bash
make logs-api                              # Tail API logs
make logs-hud                              # Tail HUD logs
curl http://localhost:8000/api/v1/health   # Health check
curl http://localhost:8000/api/v1/stats/current  # Current stats
```

## Architecture

```
api/           → FastAPI backend (see api/CLAUDE.md)
app/           → Streamlit HUD frontend (see app/CLAUDE.md)
database/      → Schema and queries (see database/CLAUDE.md)
dbt_project/   → Analytics layer (see dbt_project/CLAUDE.md)
tests/         → Test suite (see tests/CLAUDE.md)
```

## Data Flow

1. Webhook POST → API validates `X-RIFT-SECRET` header
2. Duplicate check (5-min window) → lookup gold/XP from `gamification_rules`
3. Insert to `raw_events` → return gold/XP earned
4. HUD polls `/api/v1/stats/current` every 5 seconds

## Coding Standards

- Self-explanatory code through clear naming; minimize comments
- Run `make format` before commits
- All endpoints need Pydantic schemas in `api/schemas.py`
- Database queries go through `DatabaseQueries` class

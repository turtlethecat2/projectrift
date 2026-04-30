# Project Rift (MVP bundle)

Local MVP bundle for **[Project Rift](https://github.com/texturedporcupine/projectrift)** — FastAPI webhook ingestion, PostgreSQL schema, Streamlit HUD, optional Outreach OAuth + scheduler, and dbt models.

**Layout:** keep this project **outside** the `rabbit-hole` app folder. The intended layout is a **sibling** folder next to `rabbit-hole` under the same parent (your Cursor `empty-window` project):

```text
empty-window/
  rabbit-hole/     ← separate app (do not nest Project Rift here long-term)
  projectrift/     ← this MVP (FastAPI + Streamlit + dbt)
```

**Move it on your Mac** (run in Terminal; adjust paths if yours differ):

```bash
rm -rf /Users/uly/.cursor/projects/empty-window/projectrift
mv /Users/uly/.cursor/projects/empty-window/rabbit-hole/projectrift \
   /Users/uly/.cursor/projects/empty-window/projectrift
```

Then open **`empty-window/projectrift`** as its own workspace folder in Cursor if you want it separate from Rabbit Hole.

Treat **`projectrift/`** as the unit you copy onto your machine or merge back into your fork.

## What was trimmed or fixed vs. the upstream repo

- **Docs**: One setup guide (`docs/MVP_SETUP.md`) instead of multiple overlapping markdown files.
- **Docker**: **PostgreSQL only**. Upstream `docker-compose` referenced a missing `Dockerfile.api`; for MVP, run the API + HUD on the host via `make` (or add your own Dockerfile later).
- **Database**: Added missing **`oauth_tokens`** table (required by Outreach OAuth). Fixed incorrect **`INTERVAL`** SQL in `database/queries.py`.
- **Scheduling**: Outreach polling runs **only** when OAuth env vars are real (not placeholders).
- **Python**: Declares **`pydantic-settings`**, and uses **Pydantic v2** settings validators.

## Quick path

Read **`docs/MVP_SETUP.md`** — PostgreSQL → `.env` → `make install` → `make db-migrate` → `make start-api` / `make start-hud` (or `make start`) → `make health` / `make webhook-test` → optional `make dbt-run`.

## Layout

| Path | Role |
|------|------|
| `api/` | FastAPI app |
| `app/` | Streamlit HUD |
| `database/` | `init_db.sql` + `queries.py` |
| `dbt_project/` | Staging + mart models |
| `scripts/` | Seed + cleanup + `run_dbt.sh` |

## License

MIT — match upstream unless you change it.

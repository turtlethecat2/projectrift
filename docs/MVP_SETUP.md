# Project Rift — MVP setup

Follow these steps on macOS or Linux. Install **Python 3.10+**, **PostgreSQL 14+** (or Docker), and **`psql`** on your PATH.

## 1. PostgreSQL

### Option A — Docker (recommended)

From the `projectrift` directory:

```bash
docker compose up -d postgres
```

Wait until `docker compose ps` shows `healthy` (or run `pg_isready -h localhost -p 5432`).

The compose file mounts `database/init_db.sql` **once** on first database initialization. If the volume already existed from an older run, either remove the volume (`docker compose down -v`) or apply migrations manually with **Option B**.

### Option B — Manual `psql`

Create an empty database, then:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/init_db.sql
```

(Postgres **14+** is required for `gen_random_uuid()` unless you enable `pgcrypto` instead.)

## 2. Configuration

```bash
cp .env.example .env
```

Edit `.env`:

1. **`DATABASE_URL`** — must match your Postgres user, password, host, port, and database name.
2. **`WEBHOOK_SECRET`** — at least 32 characters. Generate locally:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **`OUTREACH_*`** — optional. Leave blank or keep placeholders to disable Outreach OAuth and the background scheduler.

## 3. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Apply schema (if not done by Docker init)

```bash
make db-migrate
```

This runs `psql "$DATABASE_URL" -f database/init_db.sql`.

## 5. Run the stack

Two terminals — API and HUD:

```bash
# Terminal 1
make start-api

# Terminal 2
make start-hud
```

Or background processes + logs:

```bash
make start
tail -f logs/api.log
```

Defaults:

- API + docs: `http://127.0.0.1:8000/docs`
- HUD: `http://localhost:8501`

## 6. Smoke tests

With the API running:

```bash
make health
make webhook-test
```

Seed **without** the HTTP API (direct inserts):

```bash
make db-seed    # same as: python scripts/seed_data.py --direct
```

Seed **with** webhooks (needs API up + `faker` installed):

```bash
python scripts/seed_data.py
```

## 7. dbt (optional)

Ensure `.env` exports `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (used by `dbt_project/profiles.yml`), then:

```bash
cd dbt_project
export DBT_PROFILES_DIR=.
dbt debug
dbt run
```

Or from the repo root: `make dbt-debug` / `make dbt-run`.

dbt builds **`staging`** / **`analytics`** schemas alongside **`public`** — that is expected.

## Troubleshooting

| Issue | What to check |
|--------|----------------|
| `make db-migrate` fails | `DATABASE_URL`, Postgres running, user can create tables |
| HUD empty / DB error | `DATABASE_URL` in `.env` for Streamlit process |
| `make webhook-test` 401 | `WEBHOOK_SECRET` in `.env` matches the header sent by the Makefile |
| Outreach routes error | Configure OAuth env vars; otherwise ignore Outreach endpoints |
| Sounds missing | Optional WAV/MP3 files under `app/assets/sounds/` |

## Replacing this bundle with a git clone

To contribute upstream or pull updates:

```bash
git clone https://github.com/texturedporcupine/projectrift.git
cd projectrift
```

Compare this MVP bundle against `main` and port any fixes you still need (OAuth table, interval SQL, Makefile `-include`, compose file).

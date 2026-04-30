# Merge Outreach OAuth → Main Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Merge the completed `feature/outreach-oauth` branch into `main`, run the DB migration, and verify the app starts with real Outreach data.

**Architecture:** The feature branch adds 11 commits: APScheduler polling, OAuth token storage (`oauth_tokens` table), Outreach API client, auth + sync endpoints, and updated config. The merge is conflict-free. After merging, the DB needs the `oauth_tokens` table migration.

**Tech Stack:** Python 3.10+, FastAPI, PostgreSQL, psycopg2, APScheduler, Streamlit

---

### Task 1: Stop the currently broken app

**Files:** none

**Step 1: Stop any running processes**

```bash
make stop
```

Expected: processes stopped, no errors.

---

### Task 2: Merge the feature branch into main

**Files:** all files on `feature/outreach-oauth`

**Step 1: Make sure you're on main and it's clean**

```bash
git checkout main
git status
```

Expected: `nothing to commit, working tree clean`

**Step 2: Merge**

```bash
git merge feature/outreach-oauth --no-ff -m "feat: merge Outreach OAuth integration into main"
```

Expected: merge succeeds with no conflicts. If any conflicts appear, stop and resolve manually before continuing.

**Step 3: Verify the merge**

```bash
git log --oneline -5
```

Expected: top commit is the merge commit, followed by `feat: complete Outreach OAuth integration with polling scheduler`.

---

### Task 3: Run the oauth_tokens DB migration

**Files:** `database/oauth_tokens.sql`

**Step 1: Apply the migration**

```bash
psql $DATABASE_URL -f database/oauth_tokens.sql
```

Or if using make:

```bash
make db-migrate
```

**Step 2: Verify the table exists**

```bash
psql $DATABASE_URL -c "\d oauth_tokens"
```

Expected: table with columns `provider`, `access_token`, `refresh_token`, `expires_at`, `last_synced_at`.

---

### Task 4: Run the test suite

**Files:** `tests/test_api.py`, `tests/test_database.py`

**Step 1: Run all tests**

```bash
make test
```

Expected: all tests pass, including the new `TestOAuthTokensTable` class.

If DB-dependent tests fail because `oauth_tokens` table doesn't exist: re-run Step 3 above.

---

### Task 5: Start the app and verify

**Step 1: Start everything**

```bash
make start
```

**Step 2: Confirm API is healthy**

```bash
curl http://localhost:8000/api/v1/health
```

Expected: `{"status": "healthy", ...}`

**Step 3: Confirm Outreach OAuth settings are loaded**

```bash
curl http://localhost:8000/api/v1/outreach/status
```

Expected: JSON showing OAuth status (not connected yet if tokens not stored, but endpoint should return 200).

**Step 4: Open the HUD**

Navigate to `http://localhost:8501` — should load without errors.

---

### Task 6: Authorize Outreach OAuth (if not already done)

**Step 1: Start the OAuth flow**

Open in browser:
```
http://localhost:8000/auth/outreach/start
```

This redirects to Outreach for login + permission grant.

**Step 2: Complete the callback**

After Outreach redirects back, tokens are stored in `oauth_tokens` table automatically.

**Step 3: Trigger a manual sync to pull real data**

```bash
curl -X POST http://localhost:8000/api/v1/outreach/sync \
  -H "X-API-KEY: <your_api_key>"
```

Expected: `{"status": "ok", "events_ingested": N}` where N > 0 if you have recent Outreach activity.

**Step 4: Refresh the HUD**

Navigate to `http://localhost:8501` — should now show your real calls, connects, and meetings data.

---

### Task 7: Commit and push

**Step 1: Push main to remote**

```bash
git push origin main
```

**Step 2: Optionally delete the feature branch**

```bash
git branch -d feature/outreach-oauth
git push origin --delete feature/outreach-oauth
```

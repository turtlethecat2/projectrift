# ✅ League HUD - Export Checklist

Use this checklist when moving the project to a new environment.

## 📋 Before You Export

### 1. Save Your Rank Badge Images
- [ ] Copy all rank badge images from `app/assets/images/ranks/`
- [ ] Store them separately (USB drive, cloud storage)
- [ ] You'll need to re-add them on the new machine

### 2. Note Your Credentials
- [ ] Save your Neon database connection string (from `.env`)
- [ ] Save your webhook secret (or plan to generate a new one)
- [ ] Screenshot your Neon dashboard settings if needed
- [ ] Note your Outreach OAuth Client ID and Client Secret (you'll need to re-register if changing companies)
- [ ] Note your ngrok subdomain (if using a stable/paid ngrok URL)

### 3. Clean Up (Optional)
```bash
# Remove cache and temporary files
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
rm -rf logs/*.log
```

---

## 📦 Export Methods

### **Method 1: Compress for Transfer (Simplest)**

```bash
cd /Users/main

# Create archive (excludes secrets and cache)
tar -czf league-hud-export.tar.gz \
  --exclude=".env" \
  --exclude="venv" \
  --exclude=".venv" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude=".DS_Store" \
  --exclude="logs/*.log" \
  "League HUD"

# Check size
ls -lh league-hud-export.tar.gz

# Transfer via:
# - USB drive
# - Cloud (Dropbox, Google Drive, iCloud)
# - Email (if small enough)
```

**On new machine:**
```bash
tar -xzf league-hud-export.tar.gz
cd "League HUD"
# Follow SETUP.md
```

---

### **Method 2: Git Push to GitHub (Best for Version Control)**

```bash
cd "/Users/main/League HUD"

# Initialize git (if not done)
git init

# Add all files (excludes .env automatically via .gitignore)
git add .

# Commit
git commit -m "Initial commit - League HUD v1.0"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/league-hud.git
git branch -M main
git push -u origin main
```

**On new machine:**
```bash
git clone https://github.com/YOUR_USERNAME/league-hud.git
cd league-hud
# Follow SETUP.md
```

---

### **Method 3: VS Code Sync (For Same GitHub Account)**

1. **On current machine:**
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
   - Search: "Settings Sync: Turn On"
   - Sign in with GitHub
   - Your workspace settings will sync

2. **On new machine:**
   - Install VS Code
   - Sign in with same GitHub account
   - Settings sync automatically

**Note:** This syncs VS Code settings, not project files. Still use Method 1 or 2 for project transfer.

---

## 🆕 Setup on New Machine

### Quick Start Checklist

- [ ] **Extract/clone** project files
- [ ] **Install Python 3.10+**: `python3 --version`
- [ ] **Create virtualenv**: `python3 -m venv venv`
- [ ] **Activate venv**: `source venv/bin/activate`
- [ ] **Install deps**: `pip install -r requirements.txt`
- [ ] **Copy .env.example**: `cp .env.example .env`
- [ ] **Edit .env**: Add your DATABASE_URL, WEBHOOK_SECRET, and Outreach OAuth credentials
- [ ] **Initialize DB**: Run migration script (see SETUP.md)
- [ ] **Add rank images**: Copy to `app/assets/images/ranks/`
- [ ] **Test connection**: `python3 -c "from database.queries import DatabaseQueries; print('OK')"`
- [ ] **Start app**: `make start`
- [ ] **Verify HUD**: Open http://localhost:8501

---

## 🔐 Security Reminders

### ⚠️ **NEVER Commit These Files:**
- `.env` (contains secrets)
- `*.log` (may contain sensitive data)
- `venv/` (environment-specific)

### ✅ **Safe to Commit:**
- `.env.example` (template only)
- All code files (`*.py`)
- Configuration (`Makefile`, `docker-compose.yml`)
- Documentation (`*.md`)
- Empty directories with `.gitkeep`

---

## 📁 What's in the Export

```
league-hud-export.tar.gz
├── api/                  # FastAPI backend
├── app/                  # Streamlit HUD
│   ├── assets/
│   │   ├── images/
│   │   │   └── ranks/   # ⚠️ Empty - add your images!
│   │   └── sounds/      # Level up, gold earned sounds
│   ├── components/      # UI components
│   └── main_hud.py      # Main HUD app
├── database/
│   ├── init_db.sql      # Schema with NEW gold values
│   └── queries.py       # Updated rank system
├── scripts/
│   ├── seed_data.py     # Test data generator
│   └── cleanup_old_events.py
├── tests/               # Test suite
├── dbt_project/         # dbt transformations (optional)
├── requirements.txt     # All dependencies
├── Makefile            # Utility commands
├── README.md           # Full documentation
├── SETUP.md            # This setup guide
├── IMPLEMENTATION_REVIEW.md  # Code review & testing
├── .env.example        # Environment template
├── .gitignore          # Git ignore rules
└── docker-compose.yml  # Docker setup (optional)
```

**Total size:** ~5-10 MB (without venv)

---

## 🎯 Expected Setup Time

- **Fast track** (experienced dev): 5-10 minutes
- **Standard** (following guide carefully): 15-20 minutes
- **First time** (installing Python, etc.): 30-45 minutes

---

## 🆘 Common Export Issues

### **"No such file or directory"**
Make sure you're in the right directory:
```bash
pwd  # Should show: /Users/main/League HUD
```

### **Archive too large to email**
Use cloud storage instead:
- Google Drive: https://drive.google.com
- Dropbox: https://dropbox.com
- WeTransfer (free up to 2GB): https://wetransfer.com

### **Forgot to save database credentials**
- Go to [neon.tech](https://neon.tech)
- Sign in
- Click your project
- Copy connection string from dashboard

---

## ✅ Verification

After setup on new machine, verify:

```bash
# 1. Python environment
python3 --version  # Should be 3.10+
which python3      # Should be in venv

# 2. Dependencies installed
pip list | grep -E "fastapi|streamlit|psycopg2"

# 3. Database connection
python3 -c "from database.queries import DatabaseQueries; print('✅ DB OK')"

# 4. Environment variables
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ DATABASE_URL:', 'SET' if os.getenv('DATABASE_URL') else 'MISSING')"

# 5. Rank images (optional for now)
ls -1 app/assets/images/ranks/*.png | wc -l  # Should show 10 if images added
```

All checks passing? You're ready to grind! 🎮⚔️

---

## Changing Companies (New Outreach Instance + New Machine)

When you move to a new company with a different Outreach instance, everything credential- and environment-specific needs to be re-configured. The codebase itself does not change — only configuration.

### Full reconfiguration checklist

#### Database (Neon PostgreSQL)

| Item | Where | What to do |
|------|-------|------------|
| Neon project | [neon.tech](https://neon.tech) | Create a new Neon project (or reuse existing if personal account) |
| `DATABASE_URL` | `.env` | New connection string from Neon dashboard |
| `DB_HOST` | `.env` | Extract host from new `DATABASE_URL` |
| `DB_PORT` | `.env` | Usually `5432` (unchanged) |
| `DB_NAME` | `.env` | Extract database name from new `DATABASE_URL` |
| `DB_USER` | `.env` | Extract username from new `DATABASE_URL` |
| `DB_PASSWORD` | `.env` | Extract password from new `DATABASE_URL` |
| Schema initialization | Terminal | Run `make db-migrate` to create tables in the new database |
| `oauth_tokens` table | Terminal | Run `psql $DATABASE_URL -f database/oauth_tokens.sql` (not included in `init_db.sql`) |

#### API Security

| Item | Where | What to do |
|------|-------|------------|
| `WEBHOOK_SECRET` | `.env` | Generate a new secret: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |

#### Outreach OAuth

| Item | Where | What to do |
|------|-------|------------|
| Outreach OAuth app | New company's Outreach developer portal | Register a new OAuth application. Copy the new Client ID and Client Secret. |
| `OUTREACH_CLIENT_ID` | `.env` | Replace with the new Client ID |
| `OUTREACH_CLIENT_SECRET` | `.env` | Replace with the new Client Secret |
| `OUTREACH_REDIRECT_URI` | `.env` + Outreach app settings | Must match the ngrok URL exactly (see ngrok section below) |
| OAuth tokens in database | `oauth_tokens` table | Old tokens are invalid. Re-authorize after setup, or start with a fresh database. |

#### ngrok (OAuth callback tunnel)

| Item | Where | What to do |
|------|-------|------------|
| ngrok installation | New machine | `brew install ngrok` (macOS) |
| ngrok auth token | Terminal | `ngrok config add-authtoken YOUR_TOKEN` (get from [ngrok dashboard](https://dashboard.ngrok.com)) |
| ngrok tunnel | Terminal | `ngrok http 8000` — copy the HTTPS forwarding URL |
| Redirect URI sync | `.env` + Outreach app | The ngrok URL in `OUTREACH_REDIRECT_URI` **must exactly match** the redirect URI registered in the Outreach OAuth app. If using free ngrok, the URL changes every restart — consider a paid stable subdomain. |

#### Scheduler timezone (hardcoded)

| Item | Where | What to do |
|------|-------|------------|
| Polling timezone | `api/scheduler.py` line 37 | Hardcoded to `America/Chicago`. If your new company is in a different time zone, edit this value. The scheduler runs Mon-Fri 8am-5pm in this timezone. |

#### Python environment (new machine)

| Item | Where | What to do |
|------|-------|------------|
| Python 3.10+ | New machine | `python3 --version` to verify |
| Virtual environment | Project root | `python3 -m venv venv && source venv/bin/activate` |
| Dependencies | Terminal | `pip install -r requirements.txt` |

#### HUD assets (not in git)

| Item | Where | What to do |
|------|-------|------------|
| Rank badge images | `app/assets/images/ranks/` | Copy your 10 rank PNGs (`iron.png` through `challenger.png`). The HUD shows placeholder text without them. |
| Sound effects | `app/assets/sounds/` | `gold_gen.mp3` and `level_up.mp3` are in the repo. If you have custom sounds, copy them over. |

#### dbt (if using analytics layer)

| Item | Where | What to do |
|------|-------|------------|
| dbt connection | `dbt_project/profiles.yml` | Reads `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` from `.env` — no changes needed beyond updating those env vars. |
| dbt models | Terminal | Run `make dbt-run` after database migration to rebuild materialized tables. |

#### Items often overlooked

| Item | Where | What to do |
|------|-------|------------|
| `logs/` directory | Project root | Create `mkdir -p logs` if it doesn't exist — `make start` writes `logs/api.log` and `logs/hud.log` here. |
| `.venv` vs `venv` | Project root | The `.gitignore` ignores `venv/` but not `.venv/`. Either name works, just be consistent. |
| Old event data | `raw_events` table | If reusing a database from a previous company, consider wiping old data: `make db-reset` |
| Nooks API key | `.env` | If your new company uses Nooks, update `NOOKS_API_KEY`. |

### Step-by-step (condensed)

1. **Clone the repo** on the new machine
2. **Create venv and install deps**: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
3. **Create `.env`**: `cp .env.example .env` and fill in new Neon + Outreach credentials
4. **Initialize the database**: `make db-migrate && psql $DATABASE_URL -f database/oauth_tokens.sql`
5. **Copy rank images** to `app/assets/images/ranks/`
6. **Start ngrok**: `ngrok http 8000` — copy HTTPS URL
7. **Register Outreach OAuth app** in the new company's portal, set redirect URI to ngrok URL
8. **Update `.env`** with Outreach Client ID, Secret, and redirect URI
9. **Start the API**: `make start-api`
10. **Authorize Outreach**: Open `http://localhost:8000/auth/outreach/start` in your browser
11. **Verify**: `curl http://localhost:8000/api/v1/outreach/status`
12. **Start the HUD**: `make start` (or `make start-hud` if API is already running)

### What stays the same

- All application code (no changes needed)
- Gamification rules and rank thresholds
- HUD frontend layout and styling
- dbt model definitions
- Sound effect files (in git)
- Docker Compose config (reads from `.env`)
- Makefile commands

---

**Need help?** See [SETUP.md](SETUP.md) for detailed instructions.

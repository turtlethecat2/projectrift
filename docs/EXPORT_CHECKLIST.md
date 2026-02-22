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
- [ ] **Edit .env**: Add your DATABASE_URL and WEBHOOK_SECRET
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

**Need help?** See [SETUP.md](SETUP.md) for detailed instructions.

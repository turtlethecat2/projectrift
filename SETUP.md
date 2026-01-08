# 🎮 League HUD - Setup Guide for New Environment

This guide will help you set up the League HUD project in a new VS Code environment.

## 📦 What You Need to Copy

### **Files to Transfer:**
```
League HUD/
├── api/                    # FastAPI backend
├── app/                    # Streamlit HUD (add your rank images!)
├── database/               # Database schema and queries
├── dbt_project/            # dbt analytics (optional)
├── scripts/                # Utility scripts
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
├── Makefile               # Commands
├── README.md              # Documentation
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
└── docker-compose.yml     # Docker config (optional)
```

### **Files NOT to Copy:**
- `.env` (contains secrets - recreate on new machine)
- `venv/` or `.venv/` (virtual environment - recreate)
- `__pycache__/`, `*.pyc` (Python cache)
- `.DS_Store` (macOS files)
- `logs/` (log files)

---

## 🚀 Setup Instructions for New Environment

### **Step 1: Copy Project Files**

**Option A: Git (Recommended)**
```bash
# On current machine - initialize git and push
cd "League HUD"
git init
git add .
git commit -m "Initial commit - League HUD gamification system"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main

# On new machine - clone
git clone YOUR_GITHUB_REPO_URL
cd League-HUD
```

**Option B: Manual Copy**
```bash
# Compress the project
cd /Users/main
tar -czf league-hud.tar.gz "League HUD" --exclude=".env" --exclude="venv" --exclude="__pycache__"

# Transfer league-hud.tar.gz to new machine via:
# - USB drive
# - Cloud storage (Dropbox, Google Drive)
# - Email (if < 25MB)

# On new machine - extract
tar -xzf league-hud.tar.gz
cd "League HUD"
```

**Option C: VS Code Remote Transfer**
- Use VS Code's built-in SCP/SFTP extensions
- Or manually drag & drop folder in VS Code

---

### **Step 2: Install Prerequisites**

**Python 3.10+**
```bash
python3 --version  # Should be 3.10 or higher
```

**PostgreSQL Client (Optional)**
```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt install postgresql-client

# Windows
# Download from: https://www.postgresql.org/download/windows/
```

---

### **Step 3: Create Virtual Environment**

```bash
cd "League HUD"

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows
```

---

### **Step 4: Install Dependencies**

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI (API framework)
- Streamlit (HUD interface)
- psycopg2 (PostgreSQL driver)
- pygame (sound effects)
- pandas, plotly (analytics)
- dbt (data transformations)

---

### **Step 5: Configure Environment Variables**

```bash
# Copy the example
cp .env.example .env

# Edit .env with your values
code .env  # Or use nano, vim, etc.
```

**Required values:**

```bash
# Database - Use your Neon connection string
DATABASE_URL=postgresql://USER:PASS@HOST/DB?sslmode=require

# Generate a new webhook secret
WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# API Settings (defaults are fine)
API_HOST=0.0.0.0
API_PORT=8000

# HUD Settings
HUD_REFRESH_INTERVAL=5
SOUND_VOLUME=0.7
```

**To get your Neon connection string:**
1. Go to [neon.tech](https://neon.tech)
2. Sign in to your project
3. Copy the connection string from the dashboard
4. Paste it as `DATABASE_URL` in `.env`

---

### **Step 6: Initialize Database**

```bash
# Run the migration
python3 -c "
import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

with open('database/init_db.sql', 'r') as f:
    cur.execute(f.read())

conn.commit()
print('✅ Database initialized!')
cur.close()
conn.close()
"
```

**Verify it worked:**
```bash
python3 -c "from database.queries import DatabaseQueries; db = DatabaseQueries(); print('✅ Database connected!')"
```

---

### **Step 7: Add Rank Badge Images** ⚠️ **IMPORTANT**

```bash
# Copy your rank badge images to:
app/assets/images/ranks/

# You need these files:
# - iron.png
# - bronze.png
# - silver.png
# - gold.png
# - platinum.png
# - emerald.png
# - diamond.png
# - master.png
# - grandmaster.png
# - challenger.png
```

**Don't have the images yet?**
The app will show placeholder boxes with rank names until you add them.

---

### **Step 8: Test the Installation**

```bash
# Test database connection
python3 -c "from database.queries import DatabaseQueries; stats = DatabaseQueries().get_current_stats(); print(f'✅ Stats: {stats}')"

# Should output: ✅ Stats: {'total_gold': 0, 'total_xp': 0, ...}
```

---

### **Step 9: Start the Application**

**Option A: Using Makefile (Easiest)**
```bash
make start
```

**Option B: Manual Start**

Terminal 1 - Start API:
```bash
source venv/bin/activate
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Start HUD:
```bash
source venv/bin/activate
streamlit run app/main_hud.py
```

---

### **Step 10: Seed Test Data (Optional)**

```bash
# Generate realistic test events
python3 scripts/seed_data.py

# Choose option 2: "Seed current session (10 events)"
# This will create some dials, connects, and meetings to test with
```

---

## 🧪 Verify Everything Works

### **1. Check API Health**
```bash
curl http://localhost:8000/api/v1/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "...",
  "version": "1.0.0"
}
```

### **2. Check HUD**
- Open browser to: http://localhost:8501
- You should see the League HUD interface
- Gold: 0, XP: 0, Level: 1, Rank: Iron (with placeholder or image)

### **3. Send Test Event**
```bash
curl -X POST http://localhost:8000/api/v1/webhook/ingest \
  -H "Content-Type: application/json" \
  -H "X-RIFT-SECRET: YOUR_WEBHOOK_SECRET" \
  -d '{
    "source": "manual",
    "event_type": "call_dial",
    "metadata": {"test": true}
  }'
```

Should return:
```json
{
  "status": "success",
  "event_id": "...",
  "gold_earned": 10,
  "xp_earned": 5,
  "message": "Event processed successfully"
}
```

Watch the HUD - gold should update to 10! 🎉

---

## 🎯 Quick Reference

### **Gold Values:**
- Dial (no answer): 10g
- Pickup (connect, no meeting): 25g (stacks = 35g total)
- Meeting Set: 200g (stacks = 235g total)

### **Rank Progression (Meetings-Based):**
- 0 meetings → Iron
- 1 meeting → Bronze
- 2 meetings → Silver
- 3 meetings → Gold
- 4 meetings → Platinum
- 5 meetings → Emerald
- 6 meetings → Diamond
- 7 meetings → Master
- 8 meetings → Grandmaster
- 9+ meetings → Challenger

### **Common Commands:**
```bash
make start           # Start API + HUD
make stop            # Stop all services
make db-stats        # Show database stats
make webhook-test    # Send test webhook
make logs-api        # View API logs
make logs-hud        # View HUD logs
```

---

## ❌ Troubleshooting

### **"ModuleNotFoundError: No module named 'psycopg2'"**
```bash
pip install -r requirements.txt
```

### **"Failed to connect to database"**
- Check `DATABASE_URL` in `.env` is correct
- Verify Neon database is running
- Test connection: `psql "YOUR_DATABASE_URL" -c "SELECT 1;"`

### **"Rank badge not showing"**
- Verify images are in `app/assets/images/ranks/`
- Check file names are lowercase: `iron.png`, `bronze.png`, etc.
- Images should be PNG format

### **"Port 8000 already in use"**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or change port in .env
API_PORT=8001
```

---

## 📞 Support

If you run into issues:
1. Check [IMPLEMENTATION_REVIEW.md](IMPLEMENTATION_REVIEW.md) for detailed setup info
2. Review [README.md](README.md) for project documentation
3. Verify all environment variables are set in `.env`

---

**Built with ❤️ for SDRs grinding to Sales Engineering**

*Version: 1.0.0*
*Last Updated: 2026-01-08*

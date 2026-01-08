# ⚔️ Project Rift - SDR Gamification Engine

> Transform your SDR grind into an epic League of Legends experience

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

**Project Rift** is a real-time desktop overlay that gamifies the Sales Development Representative (SDR) workflow. It ingests sales activity logs (calls, emails, meetings), processes them using the Modern Data Stack (Postgres + dbt), and displays performance metrics via a League of Legends-inspired HUD.

## 🎯 Overview

- **Webhook API**: Secure FastAPI endpoint for real-time event ingestion
- **Gamification Engine**: Convert sales activities into Gold, XP, and Levels
- **Real-Time HUD**: League of Legends-themed overlay showing live stats
- **Analytics Layer**: dbt transformations for performance metrics and rankings
- **Sound Effects**: Audio feedback for achievements (level ups, meetings booked)

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 13+ (or [Neon.tech](https://neon.tech) account)
- Git

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd project-rift

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your actual values (DATABASE_URL, WEBHOOK_SECRET, etc.)

# 5. Initialize database
make db-migrate

# 6. (Optional) Seed test data
make db-seed

# 7. Start the application
make start
```

The API will start at `http://localhost:8000` and the HUD at `http://localhost:8501`.

## 📁 Project Structure

```
project-rift/
├── api/                    # FastAPI Backend
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration management
│   ├── schemas.py         # Pydantic models
│   ├── security.py        # Authentication & rate limiting
│   ├── database.py        # DB connection pooling
│   └── routers/           # API endpoints
├── app/                   # Streamlit HUD
│   ├── main_hud.py        # HUD application
│   ├── components/        # Reusable UI components
│   └── styles.css         # LoL-inspired styling
├── database/              # Database scripts
│   ├── init_db.sql        # Schema creation
│   └── queries.py         # Python SQL wrappers
├── dbt_project/           # dbt Analytics
│   ├── models/
│   │   ├── staging/       # Data cleaning
│   │   └── marts/         # Business logic
│   └── dbt_project.yml
├── scripts/               # Utility scripts
│   ├── seed_data.py       # Generate test data
│   ├── run_dbt.sh         # Execute dbt pipeline
│   └── cleanup_old_events.py
├── tests/                 # Test suite
└── Makefile              # Common commands
```

## 🎮 How It Works

### 1. Trigger Event
User completes a call in Nooks or Outreach.

### 2. Webhook Ingestion
External tool fires a webhook to the Project Rift API:

```bash
curl -X POST http://localhost:8000/api/v1/webhook/ingest \
  -H "Content-Type: application/json" \
  -H "X-RIFT-SECRET: your-secret-token" \
  -d '{
    "source": "nooks",
    "event_type": "call_connect",
    "metadata": {
      "prospect_name": "John Doe",
      "company": "Acme Corp",
      "call_duration": 180
    }
  }'
```

### 3. Validation & Storage
- API validates the secret header
- Pydantic validates the payload schema
- Event is stored in PostgreSQL
- Gold and XP values are looked up from `gamification_rules`

### 4. Real-Time Display
- Streamlit HUD polls the database every 5 seconds
- Gold counter updates with animation
- Sound effect plays ("coin" sound)
- XP bar progresses toward next level

### 5. Analytics
- Daily dbt runs aggregate data into performance metrics
- Rankings calculated based on gold earned
- Historical trends available for analysis

## 🏆 Gamification Rules

| Event Type | Gold | XP | Description |
|------------|------|-----|-------------|
| `call_dial` | 10 | 5 | Making a call attempt (no answer) |
| `call_connect` | 25 | 15 | Successfully connecting with prospect (no meeting) |
| `email_sent` | 10 | 3 | Sending a personalized email |
| `meeting_booked` | 200 | 100 | Scheduling a meeting |
| `meeting_attended` | 500 | 200 | Prospect attended the meeting |

**Note**: Gold values stack - a meeting booked includes dial (10g) + connect (25g) + meeting (200g) = 235g total

### Leveling System
- **1,000 XP per level**
- Level = `(Total XP / 1000) + 1`

### Rank System (Meetings-Based)
| Rank | Meetings Required |
|------|-------------------|
| Iron | 0 |
| Bronze | 1 |
| Silver | 2 |
| Gold | 3 |
| Platinum | 4 |
| Emerald | 5 |
| Diamond | 6 |
| Master | 7 |
| Grandmaster | 8 |
| Challenger | 9+ |

## 🔐 Security

### Secret Management
- All secrets stored in `.env` (never committed to Git)
- Webhook endpoint protected by `X-RIFT-SECRET` header
- Generate secret: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Rate Limiting
- 60 requests/minute per IP for webhooks
- 100 requests/minute for health checks
- Returns `429 Too Many Requests` when exceeded

### Input Validation
- Pydantic schemas enforce strict typing
- Unknown fields rejected
- Metadata limited to 5,000 characters
- Only whitelisted event types accepted

## 📊 API Endpoints

### POST `/api/v1/webhook/ingest`
Ingest sales activity events.

**Headers:**
- `Content-Type: application/json`
- `X-RIFT-SECRET: <your-secret>`

**Request Body:**
```json
{
  "source": "nooks",
  "event_type": "call_connect",
  "metadata": {
    "prospect_name": "Jane Smith",
    "company": "Tech Corp"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "gold_earned": 100,
  "xp_earned": 40,
  "message": "Event processed successfully",
  "duplicate": false
}
```

### GET `/api/v1/health`
Check system health.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-01-04T12:00:00Z",
  "version": "1.0.0"
}
```

### GET `/api/v1/stats/current`
Get current session statistics.

**Response:**
```json
{
  "total_gold": 2450,
  "total_xp": 1200,
  "current_level": 2,
  "xp_in_current_level": 200,
  "xp_to_next_level": 800,
  "events_today": 42,
  "total_events": 156,
  "rank": "Gold",
  "calls_made": 12,
  "calls_connected": 4,
  "meetings_booked": 1
}
```

## 🛠️ Development

### Available Commands

```bash
# Development
make install          # Install dependencies
make start           # Start API + HUD
make stop            # Stop all services
make restart         # Restart services

# Testing
make test            # Run all tests
make test-api        # Run API tests only
make test-db         # Run database tests
make test-webhooks   # Run webhook integration tests

# Code Quality
make format          # Format code with black/isort
make lint            # Run linting checks

# Database
make db-migrate      # Initialize database schema
make db-seed         # Seed test data
make db-reset        # Reset database (⚠️ destroys data)
make db-cleanup      # Clean up old events (dry run)
make db-stats        # Show database statistics

# dbt
make dbt-run         # Run dbt models
make dbt-test        # Run dbt tests
make dbt-docs        # Generate and serve documentation

# Utilities
make logs-api        # Tail API logs
make logs-hud        # Tail HUD logs
make health          # Check API health
make stats           # Get current stats
make webhook-test    # Send test webhook
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=api --cov=app

# Specific test file
pytest tests/test_api.py -v
```

### dbt Development

```bash
# Navigate to dbt project
cd dbt_project

# Run models
dbt run

# Run tests
dbt test

# Generate docs
dbt docs generate
dbt docs serve
```

## 🐳 Docker (Optional)

Run the entire stack with Docker Compose:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Start with pgAdmin (database management UI)
docker-compose --profile admin up -d
```

Access:
- API: http://localhost:8000
- pgAdmin: http://localhost:5050

## 🎨 HUD Customization

### Sound Effects
Place custom sound files in `app/assets/sounds/`:
- `gold_earned.mp3` - Plays when gold increases
- `level_up.mp3` - Plays on level up
- `meeting_booked.mp3` - Plays when meeting is booked

### Styling
Edit `app/styles.css` to customize colors and animations.

CSS variables:
```css
--lol-dark-blue: #010a13;
--lol-gold: #785a28;
--lol-gold-bright: #c8aa6e;
--lol-cream: #f0e6d2;
```

## 📈 Analytics with dbt

### Available Models

**Staging:**
- `stg_sales_events` - Cleaned raw events

**Marts:**
- `fct_daily_performance` - Daily aggregated metrics
- `dim_user_stats` - Lifetime user statistics

### Running Transformations

```bash
# Run all models
dbt run

# Run specific model
dbt run --select fct_daily_performance

# Test data quality
dbt test
```

## 🔧 Configuration

### Environment Variables

All configuration is managed via `.env`. See `.env.example` for all available options.

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `WEBHOOK_SECRET` - Secret for webhook authentication (min 32 chars)

**Optional:**
- `API_PORT` - API port (default: 8000)
- `HUD_REFRESH_INTERVAL` - HUD refresh rate in seconds (default: 5)
- `SOUND_VOLUME` - Sound effect volume 0.0-1.0 (default: 0.7)
- `RATE_LIMIT_PER_MINUTE` - Rate limit (default: 60)

## 🚨 Troubleshooting

### HUD Not Updating
1. Check if API is running: `make health`
2. Verify database connection: `psql $DATABASE_URL -c "SELECT 1;"`
3. Review API logs: `make logs-api`

### Webhooks Being Rejected
1. Verify `X-RIFT-SECRET` matches `.env` value
2. Check rate limit status in logs
3. Validate JSON payload structure

### Database Connection Failed
1. Ensure PostgreSQL is running
2. Verify `DATABASE_URL` in `.env`
3. Test connection: `psql $DATABASE_URL`

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (when running in development)
- **dbt Docs**: Run `make dbt-docs` and visit http://localhost:8080

## 🎯 Roadmap

### Phase 1: MVP ✅
- [x] Core webhook ingestion
- [x] Basic HUD with gold and XP
- [x] Database setup
- [x] Sound effects

### Phase 2: Polish ✅
- [x] Authentication and rate limiting
- [x] League of Legends styling
- [x] Comprehensive testing

### Phase 3: Analytics ✅
- [x] dbt project setup
- [x] Daily performance metrics
- [x] Ranking system

### Phase 4: Future Enhancements
- [ ] Team leaderboard
- [ ] Historical trend charts
- [ ] Achievements and badges
- [ ] Slack/Discord notifications
- [ ] Mobile companion app

## 🤝 Contributing

This is a portfolio project, but suggestions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Inspired by League of Legends gamification mechanics
- Built for SDRs transitioning to Sales Engineering roles
- Demonstrates Modern Data Stack proficiency (Postgres + dbt + FastAPI)

## 📧 Contact

Questions? Reach out at [your-email@example.com]

---

**Built with ❤️ for SDRs grinding their way to Sales Engineering**

*Not affiliated with or endorsed by Riot Games*

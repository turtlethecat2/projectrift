# Project Rift - Architecture & Data Flow Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [File Structure](#file-structure)
4. [Data Flow](#data-flow)
5. [Component Details](#component-details)
6. [Weekly Rank System](#weekly-rank-system)
7. [Setup & Deployment](#setup--deployment)

---

## System Overview

**Project Rift** is a League of Legends-inspired gamification system for Sales Development Representatives (SDRs). It transforms sales activities (calls, emails, meetings) into a gaming experience with XP, levels, gold, and weekly competitive ranks.

### Tech Stack
- **Backend API**: FastAPI (Python 3.13)
- **Database**: PostgreSQL (Neon.tech cloud)
- **Analytics**: dbt (data transformation)
- **Frontend HUD**: Streamlit
- **Sound Effects**: Pygame

### Core Concepts
- **Level**: Lifetime progression based on total XP earned (1000 XP per level)
- **Rank**: Weekly competitive tier based on meetings booked this week (resets Monday)
- **Gold**: Virtual currency earned from activities
- **Events**: Sales activities that trigger XP/gold rewards

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Systems                          │
│  (Outreach, Nooks, Manual API Calls, CRM Webhooks, etc.)       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ HTTP POST with webhook secret
                     │ /api/v1/webhook/ingest
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                           │
│                      (api/main.py)                               │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Webhook Router (api/routers/webhook.py)                  │  │
│  │  - Validates webhook secret                               │  │
│  │  - Checks for duplicates (idempotency)                    │  │
│  │  - Looks up gamification rules                            │  │
│  │  - Inserts event with gold/XP values                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Health Router (api/routers/health.py)                    │  │
│  │  - /health - Database connectivity check                  │  │
│  │  - /stats/current - Current user statistics               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ SQL queries via psycopg2
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database (Neon)                      │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Raw Tables                                               │  │
│  │  - raw_events: All events with gold/XP values            │  │
│  │  - gamification_rules: Event type → gold/XP mapping      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  dbt Models (views/tables)                                │  │
│  │  - stg_sales_events: Cleaned staging layer               │  │
│  │  - dim_user_stats: Aggregated user statistics            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ Queries stats every 5 seconds
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit HUD (app/main_hud.py)              │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Components:                                              │  │
│  │  - Gold Counter (gold_counter.py)                        │  │
│  │  - XP Bar (xp_bar.py)                                    │  │
│  │  - Level Badge                                            │  │
│  │  - Rank Badge with Icon + Text                           │  │
│  │  - KDA Display (kda_display.py)                          │  │
│  │  - Event Counts                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Sound Effects (Pygame):                                  │  │
│  │  - gold_gen.mp3: When gold earned                        │  │
│  │  - level_up.mp3: When level up or meeting booked         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
projectrift/
├── api/                          # Backend API
│   ├── __init__.py              # Version info
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Environment config (Pydantic settings)
│   ├── database.py              # Connection pool management
│   ├── schemas.py               # Pydantic models for API
│   ├── security.py              # Webhook auth, rate limiting
│   └── routers/
│       ├── webhook.py           # Event ingestion endpoint
│       └── health.py            # Health check & stats endpoints
│
├── app/                          # Frontend HUD
│   ├── main_hud.py              # Main Streamlit application
│   ├── styles.css               # LoL-inspired CSS styling
│   ├── assets/
│   │   ├── fonts/               # Beaufort for LOL fonts
│   │   ├── images/ranks/        # Rank icon PNGs
│   │   └── sounds/              # Sound effect MP3s
│   └── components/
│       ├── gold_counter.py      # Gold display component
│       ├── xp_bar.py            # XP bar, level & rank badges
│       └── kda_display.py       # Stats display components
│
├── database/                     # Database layer
│   ├── __init__.py
│   ├── init_db.sql              # Schema initialization SQL
│   └── queries.py               # DatabaseQueries class
│
├── dbt_project/                  # dbt analytics
│   ├── dbt_project.yml          # dbt config
│   ├── profiles.yml             # Database connection config
│   └── models/
│       ├── staging/
│       │   └── stg_sales_events.sql  # Cleaned events
│       └── marts/
│           └── dim_user_stats.sql    # User aggregates
│
├── scripts/                      # Utility scripts
│   └── seed_data.py             # Database seeding script
│
├── .env                          # Environment variables (NOT in git)
├── .env.example                 # Template for .env
├── requirements.txt             # Python dependencies
├── Makefile                     # Development commands
└── README.md                    # User guide
```

---

## Data Flow

### Event Ingestion Flow (When a New Event Occurs)

```
1. External System Sends Event
   ↓
   POST /api/v1/webhook/ingest
   Headers: X-RIFT-SECRET: {webhook_secret}
   Body: {
     "source": "outreach",
     "event_type": "meeting_booked",
     "metadata": {...}
   }

2. API Gateway (api/main.py)
   ↓
   - CORS middleware
   - Rate limiting (60 req/min)
   - Request logging

3. Webhook Router (api/routers/webhook.py)
   ↓
   ingest_event() function:

   a. Security Check
      - verify_webhook_secret() validates X-RIFT-SECRET header
      - Returns 401 if invalid

   b. Duplicate Detection (Idempotency)
      - db.check_duplicate_event() checks for same event in last 5 minutes
      - If duplicate: returns success with duplicate=True, gold=0, xp=0

   c. Lookup Gamification Rules
      - db.get_gamification_rule(event_type)
      - Queries gamification_rules table
      - Returns gold_value and xp_value for this event type
      - If no rule found: returns 422 error

   d. Insert Event
      - db.insert_event() writes to raw_events table
      - Columns: event_id, source, event_type, gold_value, xp_value, metadata, created_at
      - Returns unique event_id (UUID)

   e. Return Response
      - 201 status code
      - Body: {
          "status": "success",
          "event_id": "...",
          "gold_earned": 100,
          "xp_earned": 50,
          "message": "Event processed successfully",
          "duplicate": false
        }

4. Database (PostgreSQL)
   ↓
   - raw_events table gets new row
   - Triggers propagate to dbt models (if using materialized views)

5. HUD Polling (Every 5 Seconds)
   ↓
   - DatabaseQueries.get_current_stats() queries raw_events
   - Aggregates:
     * Total gold (SUM)
     * Total XP (SUM)
     * Current level (XP / 1000 + 1)
     * Weekly meetings booked (COUNT WHERE created_at >= Monday)
     * Rank calculation (based on weekly meetings)

6. HUD Updates
   ↓
   - Compares new stats to previous stats
   - If gold increased: plays gold_gen.mp3
   - If level increased: plays level_up.mp3, shows balloons
   - If meeting booked: plays level_up.mp3
   - If rank increased: shows balloons
   - Updates UI components with new values
```

### Query Flow for HUD Display

```
HUD Refresh (every 5 seconds)
↓
database/queries.py → DatabaseQueries.get_current_stats()
↓
SQL Query:
  SELECT
    COALESCE(SUM(gold_value), 0) AS total_gold,
    COALESCE(SUM(xp_value), 0) AS total_xp,
    COUNT(*) AS total_events,
    COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) AS events_today,
    SUM(CASE WHEN event_type = 'call_dial' THEN 1 ELSE 0 END) AS calls_made,
    SUM(CASE WHEN event_type = 'call_connect' THEN 1 ELSE 0 END) AS calls_connected,
    SUM(CASE WHEN event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS meetings_booked,
    -- Weekly meetings for rank calculation
    SUM(CASE
      WHEN created_at >= DATE_TRUNC('week', CURRENT_DATE)
      AND event_type = 'meeting_booked'
      THEN 1 ELSE 0
    END) AS weekly_meetings_booked
  FROM raw_events
↓
Python Processing:
  - Calculate current_level = int(total_xp / 1000) + 1
  - Calculate xp_in_current_level = total_xp % 1000
  - Calculate xp_to_next_level = 1000 - (total_xp % 1000)
  - Calculate rank = _calculate_rank(weekly_meetings_booked)
↓
Return stats dictionary to HUD
↓
HUD renders components with updated values
```

---

## Component Details

### 1. API Layer (api/)

#### **api/main.py**
- **Purpose**: FastAPI application entry point
- **What it does**:
  - Creates FastAPI app instance
  - Configures CORS (allows frontend to call API)
  - Sets up rate limiting with SlowAPI
  - Includes routers (webhook, health)
  - Configures logging
  - Startup/shutdown events for database pool

#### **api/config.py**
- **Purpose**: Environment configuration management
- **What it does**:
  - Loads .env file using python-dotenv
  - Defines Settings class with Pydantic for validation
  - Validates WEBHOOK_SECRET (must be 32+ chars)
  - Validates SOUND_VOLUME and HUD_OPACITY (0.0-1.0)
  - Provides global `settings` instance

#### **api/database.py**
- **Purpose**: PostgreSQL connection pool
- **What it does**:
  - Creates psycopg2 connection pool (min=2, max=10 connections)
  - Provides get_db_pool() function for connection reuse
  - check_database_health() for health checks
  - Optimizes connection management for concurrent requests

#### **api/schemas.py**
- **Purpose**: Pydantic models for API validation
- **Models**:
  - `EventPayload`: Incoming webhook data
  - `EventResponse`: API response after event processing
  - `HealthResponse`: Health check response
  - `CurrentStats`: User statistics response

#### **api/security.py**
- **Purpose**: Authentication and rate limiting
- **What it does**:
  - verify_webhook_secret() dependency: checks X-RIFT-SECRET header
  - SlowAPI limiter configuration (60 requests/minute)
  - get_rate_limit_for_endpoint() returns rate limit string

#### **api/routers/webhook.py**
- **Purpose**: Event ingestion endpoint
- **Key Function**: `ingest_event(request, payload, _)`
  1. Validates webhook secret
  2. Checks for duplicate events (5-minute window)
  3. Looks up gamification rule for event_type
  4. Inserts event with gold/XP values
  5. Returns EventResponse with rewards
- **Error Handling**:
  - 401: Invalid webhook secret
  - 422: No gamification rule for event type
  - 500: Database or processing error

#### **api/routers/health.py**
- **Purpose**: Health check and statistics
- **Endpoints**:
  - `GET /api/v1/health`: Database connectivity check
  - `GET /api/v1/stats/current`: Current user stats (gold, XP, level, rank)

### 2. Database Layer (database/)

#### **database/init_db.sql**
- **Purpose**: Database schema initialization
- **Tables Created**:
  - `raw_events`: Stores all events with gold/XP values
  - `gamification_rules`: Maps event types to rewards
  - Indexes for performance (event_type, created_at)
- **Default Rules**:
  - call_dial: 5 gold, 10 XP
  - call_connect: 25 gold, 50 XP
  - email_sent: 3 gold, 5 XP
  - meeting_booked: 100 gold, 200 XP
  - meeting_attended: 150 gold, 300 XP

#### **database/queries.py**
- **Purpose**: Database query abstraction
- **Class**: `DatabaseQueries`
- **Key Methods**:
  - `get_current_stats()`: Aggregates all user statistics
  - `get_daily_stats(days)`: Daily breakdown for charts
  - `get_recent_events(limit)`: Recent activity feed
  - `check_duplicate_event()`: Idempotency check
  - `get_gamification_rule()`: Lookup gold/XP for event type
  - `insert_event()`: Write new event to database
  - `_calculate_rank()`: Convert weekly meetings to rank tier

### 3. Analytics Layer (dbt_project/)

#### **dbt_project/models/staging/stg_sales_events.sql**
- **Purpose**: Cleaned staging layer
- **What it does**:
  - Selects from raw_events
  - Casts data types
  - Adds calculated fields
  - Provides clean interface for marts

#### **dbt_project/models/marts/dim_user_stats.sql**
- **Purpose**: User statistics aggregation
- **What it does**:
  - Creates CTEs for:
    - `lifetime_stats`: All-time aggregates
    - `weekly_stats`: Current week meetings (for rank)
    - `current_level`: Level calculation from XP
    - `current_rank`: Rank tier from weekly meetings
    - `performance_metrics`: Rates and averages
  - Joins all CTEs with CROSS JOIN
  - Materializes as table for fast queries

### 4. Frontend Layer (app/)

#### **app/main_hud.py**
- **Purpose**: Main HUD application
- **What it does**:
  - Initializes Streamlit page config
  - Loads custom CSS from styles.css
  - Initializes pygame mixer for sounds
  - Main loop:
    1. Queries database for current stats
    2. Compares to previous stats (session state)
    3. Detects changes (level up, gold earned, meeting booked)
    4. Plays appropriate sound effects
    5. Renders UI components
    6. Sleeps 5 seconds
    7. Reruns (st.rerun())

#### **app/components/gold_counter.py**
- **Purpose**: Display gold amount
- **What it does**:
  - Renders gold coin icon
  - Shows total gold value with formatting
  - Applies LoL gold color styling

#### **app/components/xp_bar.py**
- **Purpose**: XP bar, level badge, rank badge
- **Functions**:
  - `render_xp_bar()`: Animated progress bar to next level
  - `render_level_badge()`: Shows "Lvl X" badge
  - `render_rank_badge()`: Shows rank icon + text label

#### **app/components/kda_display.py**
- **Purpose**: Stats display (calls, meetings, etc.)
- **Functions**:
  - `render_kda_display()`: Main stats (calls made/connected, meetings)
  - `render_event_counts()`: Event breakdown by type

#### **app/styles.css**
- **Purpose**: LoL-inspired styling
- **What it includes**:
  - Font-face declarations for Beaufort for LOL
  - CSS variables for LoL color palette
  - Component styles (gold counter, XP bar, badges)
  - Animations (fadeIn, pulse)
  - Responsive design for different screen sizes

---

## Weekly Rank System

### How Weekly Ranks Work

**Rank Calculation**:
```python
def _calculate_rank(meetings_booked: int) -> str:
    rank_map = {
        0: 'Iron',
        1: 'Bronze',
        2: 'Silver',
        3: 'Gold',
        4: 'Platinum',
        5: 'Emerald',
        6: 'Diamond',
        7: 'Master',
        8: 'Grandmaster',
        9: 'Challenger'  # 9+ meetings
    }
    if meetings_booked >= 9:
        return 'Challenger'
    return rank_map.get(meetings_booked, 'Iron')
```

**SQL Query for Weekly Meetings**:
```sql
SUM(CASE
  WHEN created_at >= DATE_TRUNC('week', CURRENT_DATE)
  AND event_type = 'meeting_booked'
  THEN 1
  ELSE 0
END) AS weekly_meetings_booked
```

**Key Points**:
- Week starts on Monday (PostgreSQL DATE_TRUNC('week') default)
- Only `meeting_booked` events count toward rank
- Ranks reset automatically every Monday at 00:00:00
- Real-time: Updates immediately when new meeting logged
- Competitive: Encourages consistent weekly performance

**dbt Model Weekly Stats**:
```sql
weekly_stats AS (
    SELECT
        SUM(CASE
            WHEN created_at >= DATE_TRUNC('week', CURRENT_DATE)
            AND event_type = 'meeting_booked'
            THEN 1
            ELSE 0
        END) AS weekly_meetings_booked
    FROM {{ ref('stg_sales_events') }}
)
```

---

## Setup & Deployment

### Local Development Workflow

1. **Environment Setup**:
   ```bash
   # Create virtual environment
   python3.13 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Copy environment template
   cp .env.example .env
   # Edit .env with your DATABASE_URL and WEBHOOK_SECRET
   ```

2. **Database Initialization**:
   ```bash
   # Create schema and seed rules
   make db-migrate

   # (Optional) Add test data
   make db-seed
   ```

3. **Start Services**:
   ```bash
   # Terminal 1: Start API
   make start-api

   # Terminal 2: Start HUD
   make start-hud
   ```

4. **Test Event Ingestion**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/webhook/ingest \
     -H "Content-Type: application/json" \
     -H "X-RIFT-SECRET: your_webhook_secret" \
     -d '{
       "source": "manual",
       "event_type": "meeting_booked",
       "metadata": {"test": true}
     }'
   ```

### Production Deployment

**API Server**:
- Deploy FastAPI with Uvicorn on cloud (Heroku, Railway, Fly.io)
- Set environment variables in platform dashboard
- Use PostgreSQL connection pooling for concurrency
- Enable HTTPS and set CORS origins

**HUD**:
- Deploy Streamlit app separately or as internal tool
- Configure DATABASE_URL to point to production database
- Adjust REFRESH_INTERVAL for production load
- Consider authentication for multi-user scenarios

**Database**:
- Use Neon.tech (serverless PostgreSQL) for easy scaling
- Set up automated backups
- Run dbt models on schedule (e.g., daily via GitHub Actions)

---

## Troubleshooting

### Common Issues

**1. Module Import Errors**:
- **Symptom**: `ModuleNotFoundError: No module named 'database'`
- **Fix**: Ensure `PYTHONPATH=.` when running Streamlit (already in Makefile)

**2. Rate Limiter Errors**:
- **Symptom**: `No "request" argument on function`
- **Fix**: Add `request: Request` parameter to endpoints using `@limiter.limit()`

**3. Database Connection Issues**:
- **Symptom**: `connection refused` or timeout
- **Fix**: Check DATABASE_URL in .env, verify Neon database is running

**4. Webhook Authentication Fails**:
- **Symptom**: 401 Unauthorized
- **Fix**: Ensure X-RIFT-SECRET header matches WEBHOOK_SECRET in .env

**5. Rank Not Updating**:
- **Symptom**: Rank stays at Iron despite meetings
- **Fix**: Check that meetings were logged THIS WEEK (after Monday 00:00)

---

## Performance Considerations

**Database Queries**:
- raw_events table indexed on (event_type, created_at)
- Connection pool reuses connections (min=2, max=10)
- get_current_stats() uses aggregation (no table scan)

**HUD Refresh**:
- 5-second interval balances responsiveness vs. load
- Can be adjusted via HUD_REFRESH_INTERVAL env var
- Consider caching for multi-user deployments

**API Rate Limiting**:
- 60 requests/minute default (adjustable)
- Prevents abuse and database overload
- Returns 429 Too Many Requests when exceeded

---

## Future Enhancements

**Potential Features**:
- Multi-user support with user_id tracking
- Leaderboards (top SDRs by rank/gold/XP)
- Achievements and badges
- Team competitions
- Historical rank tracking (rank history by week)
- Email/Slack notifications for rank changes
- Customizable gamification rules via UI
- Integration with CRM systems (Salesforce, HubSpot)

---

## Questions?

For issues or questions:
- GitHub Issues: https://github.com/[your-username]/projectrift/issues
- Documentation: See README.md for user guide
- Architecture: This file (ARCHITECTURE.md)

---

**Last Updated**: 2026-01-11
**Version**: 1.0
**Author**: Project Rift Team

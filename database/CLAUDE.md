# database/CLAUDE.md

Database layer - PostgreSQL schema and Python query abstraction.

## Structure

```
init_db.sql   → Schema creation (raw_events, gamification_rules, event_log)
queries.py    → DatabaseQueries class (all SQL operations)
```

## Schema

**raw_events** - All ingested events
```sql
id            UUID PRIMARY KEY
source        VARCHAR(50)      -- outreach, nooks, manual, zapier
event_type    VARCHAR(50)      -- call_dial, call_connect, etc.
gold_value    INTEGER
xp_value      INTEGER
metadata      JSONB
created_at    TIMESTAMP
```

**gamification_rules** - Event type → reward mapping
```sql
event_type    VARCHAR(50) PRIMARY KEY
gold_value    INTEGER
xp_value      INTEGER
display_name  VARCHAR(100)
description   TEXT
```

**event_log** - Audit trail
```sql
id            SERIAL PRIMARY KEY
event_id      UUID REFERENCES raw_events(id)
action        VARCHAR(50)
details       JSONB
created_at    TIMESTAMP
```

## Default Gamification Rules

| event_type | gold | xp |
|------------|------|-----|
| call_dial | 10 | 5 |
| call_connect | 25 | 15 |
| email_sent | 10 | 3 |
| meeting_booked | 200 | 100 |
| meeting_attended | 500 | 200 |

## DatabaseQueries Class

Key methods in `queries.py`:
- `insert_event()` - Insert new event, returns UUID
- `get_gamification_rule()` - Lookup gold/XP for event type
- `get_current_stats()` - Aggregate stats (total gold, XP, level, rank)
- `check_duplicate_event()` - 5-minute dedup window
- `cleanup_old_events()` - Delete events older than N days

**Pattern:** All methods create/close their own connections. No connection pooling at this layer (handled in `api/database.py` for the API).

## Rank Calculation

Ranks based on **weekly** meetings booked (resets Monday):
```
0 meetings = Iron       5 meetings = Emerald
1 meeting  = Bronze     6 meetings = Diamond
2 meetings = Silver     7 meetings = Master
3 meetings = Gold       8 meetings = Grandmaster
4 meetings = Platinum   9+ meetings = Challenger
```

## Commands

```bash
make db-migrate    # Run init_db.sql
make db-seed       # Seed test data
make db-reset      # Drop and recreate (destructive)
make db-stats      # Show statistics
```

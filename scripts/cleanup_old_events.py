#!/usr/bin/env python3
"""Delete old raw_events or print stats."""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv()

from database.queries import DatabaseQueries  # noqa: E402


def cleanup_old_events(days: int, dry_run: bool) -> None:
    print(f"Retention: keep last {days} days")
    cutoff = datetime.now() - timedelta(days=days)
    print(f"Cutoff: {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")

    import psycopg2

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM raw_events WHERE created_at < %s", (cutoff,)
    )
    (count,) = cur.fetchone()
    cur.close()
    conn.close()

    print(f"Matching rows: {count}")
    if dry_run:
        return

    db = DatabaseQueries()
    deleted = db.cleanup_old_events(days=days)
    print(f"Deleted: {deleted}")


def show_stats() -> None:
    db = DatabaseQueries()
    stats = db.get_current_stats()
    print("Database statistics")
    print("-" * 40)
    for k in sorted(stats.keys()):
        print(f"{k}: {stats[k]}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--stats", action="store_true")
    args = p.parse_args()

    if args.stats:
        show_stats()
    else:
        cleanup_old_events(args.days, args.dry_run)


if __name__ == "__main__":
    main()

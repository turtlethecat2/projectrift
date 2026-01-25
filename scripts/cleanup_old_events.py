#!/usr/bin/env python3
"""
Cleanup old events from the database
Removes events older than the specified retention period
"""

import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv

# Add parent directory to path to import database module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.queries import DatabaseQueries

load_dotenv()

# Configuration
DEFAULT_RETENTION_DAYS = int(os.getenv("RAW_EVENTS_RETENTION_DAYS", 90))


def cleanup_old_events(days: int = DEFAULT_RETENTION_DAYS, dry_run: bool = False):
    """
    Clean up events older than specified days

    Args:
        days: Number of days to keep (older events will be deleted)
        dry_run: If True, only show what would be deleted without actually deleting
    """
    print("=" * 60)
    print("Project Rift - Event Cleanup Script")
    print("=" * 60)
    print(f"Retention period: {days} days")
    print(
        f"Cutoff date: {(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')}"
    )
    print(
        f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (events will be deleted)'}"
    )
    print("=" * 60)

    try:
        db = DatabaseQueries()

        if dry_run:
            # Count events that would be deleted
            import psycopg2

            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            cur = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days)
            query = """
                SELECT COUNT(*) FROM raw_events
                WHERE created_at < %s
            """
            cur.execute(query, (cutoff_date,))
            count = cur.fetchone()[0]

            cur.close()
            conn.close()

            print(f"\n📊 Found {count} events older than {days} days")
            print("   (These would be deleted in live mode)")

            if count > 0:
                print(
                    "\n⚠️  To actually delete these events, run without --dry-run flag"
                )

        else:
            # Actually delete old events
            print("\n🗑️  Deleting old events...")
            deleted_count = db.cleanup_old_events(days=days)

            print(f"✅ Deleted {deleted_count} events older than {days} days")

            if deleted_count > 0:
                print(f"   Freed up database space")
                print(
                    f"   Events created after {(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')} were kept"
                )

    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Cleanup complete!")
    print("=" * 60)


def show_database_stats():
    """Show current database statistics"""
    print("\n📊 Database Statistics:")
    print("-" * 60)

    try:
        db = DatabaseQueries()
        stats = db.get_current_stats()

        print(f"Total events: {stats.get('total_events', 0):,}")
        print(f"Events today: {stats.get('events_today', 0):,}")
        print(f"Total gold: {stats.get('total_gold', 0):,}")
        print(f"Total XP: {stats.get('total_xp', 0):,}")
        print(f"Current level: {stats.get('current_level', 1)}")
        print(f"Current rank: {stats.get('rank', 'Unknown')}")

    except Exception as e:
        print(f"Error retrieving stats: {e}")

    print("-" * 60)


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up old events from Project Rift database"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Keep events from last N days (default: {DEFAULT_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument("--stats", action="store_true", help="Show database statistics")

    args = parser.parse_args()

    if args.stats:
        show_database_stats()
    else:
        cleanup_old_events(days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

"""
Database query functions for Project Rift
Provides Python wrappers for common SQL operations
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv

load_dotenv()


class DatabaseQueries:
    """Handles all database query operations"""

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection

        Args:
            connection_string: PostgreSQL connection string (uses env var if not provided)
        """
        self.connection_string = connection_string or os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("DATABASE_URL not found in environment variables")

    def get_connection(self):
        """Create a new database connection"""
        return psycopg2.connect(self.connection_string)

    def insert_event(
        self,
        source: str,
        event_type: str,
        gold_value: int,
        xp_value: int,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Insert a new event into raw_events table

        Args:
            source: Event source (outreach, nooks, manual, zapier)
            event_type: Type of event (call_dial, call_connect, etc.)
            gold_value: Gold amount to award
            xp_value: XP amount to award
            metadata: Optional JSON metadata

        Returns:
            UUID of created event
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            query = """
                INSERT INTO raw_events (source, event_type, gold_value, xp_value, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            cur.execute(query, (source, event_type, gold_value, xp_value, Json(metadata or {})))
            event_id = cur.fetchone()[0]
            conn.commit()

            # Log the creation
            self.log_event_action(event_id, 'created', {'source': source, 'event_type': event_type})

            return str(event_id)

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def log_event_action(
        self,
        event_id: str,
        action: str,
        details: Dict[str, Any] = None
    ) -> None:
        """
        Log an action to the event_log table

        Args:
            event_id: UUID of the event
            action: Action type (created, processed, failed)
            details: Optional JSON details
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            query = """
                INSERT INTO event_log (event_id, action, details)
                VALUES (%s, %s, %s)
            """
            cur.execute(query, (event_id, action, Json(details or {})))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def get_gamification_rule(self, event_type: str) -> Optional[Dict[str, Any]]:
        """
        Get gold and XP values for a given event type

        Args:
            event_type: Type of event

        Returns:
            Dictionary with gold_value and xp_value, or None if not found
        """
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            query = """
                SELECT event_type, gold_value, xp_value, display_name, description
                FROM gamification_rules
                WHERE event_type = %s
            """
            cur.execute(query, (event_type,))
            result = cur.fetchone()
            return dict(result) if result else None
        finally:
            cur.close()
            conn.close()

    def get_current_stats(self) -> Dict[str, Any]:
        """
        Get current session statistics

        Returns:
            Dictionary with total_gold, total_xp, events_today, etc.
        """
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            query = """
                SELECT
                    COALESCE(SUM(gold_value), 0) AS total_gold,
                    COALESCE(SUM(xp_value), 0) AS total_xp,
                    COUNT(*) AS total_events,
                    COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) AS events_today,
                    SUM(CASE WHEN event_type = 'call_dial' THEN 1 ELSE 0 END) AS calls_made,
                    SUM(CASE WHEN event_type = 'call_connect' THEN 1 ELSE 0 END) AS calls_connected,
                    SUM(CASE WHEN event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS meetings_booked
                FROM raw_events
            """
            cur.execute(query)
            result = cur.fetchone()

            stats = dict(result) if result else {}

            # Calculate level and rank
            total_xp = stats.get('total_xp', 0)
            total_gold = stats.get('total_gold', 0)

            stats['current_level'] = int(total_xp / 1000) + 1
            stats['xp_in_current_level'] = total_xp % 1000
            stats['xp_to_next_level'] = 1000 - (total_xp % 1000)
            stats['rank'] = self._calculate_rank(stats.get('meetings_booked', 0))

            return stats

        finally:
            cur.close()
            conn.close()

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily statistics for the past N days

        Args:
            days: Number of days to retrieve

        Returns:
            List of daily statistics dictionaries
        """
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            query = """
                SELECT
                    DATE(created_at) AS event_date,
                    COUNT(*) AS total_events,
                    SUM(gold_value) AS total_gold,
                    SUM(xp_value) AS total_xp,
                    SUM(CASE WHEN event_type = 'call_dial' THEN 1 ELSE 0 END) AS calls_made,
                    SUM(CASE WHEN event_type = 'call_connect' THEN 1 ELSE 0 END) AS calls_connected,
                    SUM(CASE WHEN event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS meetings_booked
                FROM raw_events
                WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) DESC
            """
            cur.execute(query, (days,))
            results = cur.fetchall()
            return [dict(row) for row in results]

        finally:
            cur.close()
            conn.close()

    def cleanup_old_events(self, days: int = 90) -> int:
        """
        Delete events older than specified days

        Args:
            days: Age threshold in days

        Returns:
            Number of deleted events
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = """
                DELETE FROM raw_events
                WHERE created_at < %s
                RETURNING id
            """
            cur.execute(query, (cutoff_date,))
            deleted_count = cur.rowcount
            conn.commit()
            return deleted_count

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def check_duplicate_event(
        self,
        source: str,
        event_type: str,
        metadata: Dict[str, Any],
        minutes: int = 5
    ) -> bool:
        """
        Check if a duplicate event exists within the specified time window

        Args:
            source: Event source
            event_type: Event type
            metadata: Event metadata
            minutes: Time window in minutes

        Returns:
            True if duplicate exists, False otherwise
        """
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            query = """
                SELECT COUNT(*) FROM raw_events
                WHERE source = %s
                AND event_type = %s
                AND metadata = %s
                AND created_at >= NOW() - INTERVAL '%s minutes'
            """
            cur.execute(query, (source, event_type, Json(metadata), minutes))
            count = cur.fetchone()[0]
            return count > 0

        finally:
            cur.close()
            conn.close()

    @staticmethod
    def _calculate_rank(meetings_booked: int) -> str:
        """
        Calculate rank based on meetings booked

        Args:
            meetings_booked: Total meetings booked

        Returns:
            Rank name (Iron, Bronze, Silver, Gold, Platinum, Emerald, Diamond, Master, Grandmaster, Challenger)
        """
        # Exact meeting count to rank mapping
        rank_map = {
            0: 'Iron',
            1: 'Bronze',
            2: 'Silver',
            3: 'Gold',
            4: 'Platinum',
            5: 'Emerald',
            6: 'Diamond',
            7: 'Master',
            8: 'Grandmaster'
        }

        # 9 or more meetings = Challenger
        if meetings_booked >= 9:
            return 'Challenger'

        return rank_map.get(meetings_booked, 'Iron')


# Convenience function for getting a database instance
def get_db() -> DatabaseQueries:
    """Get a DatabaseQueries instance"""
    return DatabaseQueries()

"""Database helpers — raw psycopg2 connections (scripts + API-adjacent queries)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, RealDictCursor

load_dotenv()


class DatabaseQueries:
    """CRUD and reporting against Project Rift tables."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("DATABASE_URL not found in environment variables")

    @contextmanager
    def _transaction(
        self, *, dict_rows: bool = False
    ) -> Generator[tuple, None, None]:
        conn = psycopg2.connect(self.connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor if dict_rows else None)
        try:
            yield conn, cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def insert_event(
        self,
        source: str,
        event_type: str,
        gold_value: int,
        xp_value: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        with self._transaction() as (_, cur):
            cur.execute(
                """
                INSERT INTO raw_events (source, event_type, gold_value, xp_value, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (source, event_type, gold_value, xp_value, Json(metadata or {})),
            )
            event_id = cur.fetchone()[0]

        self.log_event_action(
            event_id, "created", {"source": source, "event_type": event_type}
        )
        return str(event_id)

    def log_event_action(
        self, event_id: str, action: str, details: Dict[str, Any] | None = None
    ) -> None:
        with self._transaction() as (_, cur):
            cur.execute(
                """
                INSERT INTO event_log (event_id, action, details)
                VALUES (%s, %s, %s)
                """,
                (event_id, action, Json(details or {})),
            )

    def get_gamification_rule(self, event_type: str) -> Optional[Dict[str, Any]]:
        with self._transaction(dict_rows=True) as (_, cur):
            cur.execute(
                """
                SELECT event_type, gold_value, xp_value, display_name, description
                FROM gamification_rules
                WHERE event_type = %s
                """,
                (event_type,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_current_stats(self) -> Dict[str, Any]:
        with self._transaction(dict_rows=True) as (_, cur):
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(gold_value), 0) AS total_gold,
                    COALESCE(SUM(xp_value), 0) AS total_xp,
                    COUNT(*) AS total_events,
                    COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) AS events_today,
                    SUM(CASE WHEN event_type = 'call_dial' THEN 1 ELSE 0 END) AS calls_made,
                    SUM(CASE WHEN event_type = 'call_connect' THEN 1 ELSE 0 END) AS calls_connected,
                    SUM(CASE WHEN event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS meetings_booked
                FROM raw_events
                WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
                """
            )
            row = cur.fetchone()
            stats = dict(row) if row else {}

        total_xp = stats.get("total_xp", 0) or 0
        meetings_booked = int(stats.get("meetings_booked") or 0)

        stats["current_level"] = int(total_xp / 1000) + 1
        stats["xp_in_current_level"] = int(total_xp % 1000)
        stats["xp_to_next_level"] = 1000 - (int(total_xp) % 1000)
        stats["rank"] = self._calculate_rank(meetings_booked)
        return stats

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        with self._transaction(dict_rows=True) as (_, cur):
            cur.execute(
                """
                SELECT
                    DATE(created_at) AS event_date,
                    COUNT(*) AS total_events,
                    SUM(gold_value) AS total_gold,
                    SUM(xp_value) AS total_xp,
                    SUM(CASE WHEN event_type = 'call_dial' THEN 1 ELSE 0 END) AS calls_made,
                    SUM(CASE WHEN event_type = 'call_connect' THEN 1 ELSE 0 END) AS calls_connected,
                    SUM(CASE WHEN event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS meetings_booked
                FROM raw_events
                WHERE created_at >= CURRENT_DATE - (%s::integer * INTERVAL '1 day')
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) DESC
                """,
                (days,),
            )
            return [dict(r) for r in cur.fetchall()]

    def cleanup_old_events(self, days: int = 90) -> int:
        cutoff_date = datetime.now() - timedelta(days=days)
        with self._transaction() as (_, cur):
            cur.execute(
                """
                DELETE FROM raw_events
                WHERE created_at < %s
                RETURNING id
                """,
                (cutoff_date,),
            )
            return cur.rowcount

    def check_duplicate_event(
        self, source: str, event_type: str, metadata: Dict[str, Any], minutes: int = 5
    ) -> bool:
        with self._transaction() as (_, cur):
            cur.execute(
                """
                SELECT COUNT(*) FROM raw_events
                WHERE source = %s
                  AND event_type = %s
                  AND metadata = %s
                  AND created_at >= NOW() - (%s::integer * INTERVAL '1 minute')
                """,
                (source, event_type, Json(metadata), minutes),
            )
            (count,) = cur.fetchone()
            return count > 0

    def save_oauth_tokens(
        self,
        provider: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
    ) -> None:
        with self._transaction() as (_, cur):
            cur.execute(
                """
                INSERT INTO oauth_tokens (provider, access_token, refresh_token, expires_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (provider) DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
                """,
                (provider, access_token, refresh_token, expires_at),
            )

    def load_oauth_tokens(self, provider: str) -> Optional[Dict[str, Any]]:
        with self._transaction(dict_rows=True) as (_, cur):
            cur.execute(
                "SELECT access_token, refresh_token, expires_at FROM oauth_tokens WHERE provider = %s",
                (provider,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def update_last_synced_at(self, provider: str, synced_at: datetime) -> None:
        with self._transaction() as (_, cur):
            cur.execute(
                "UPDATE oauth_tokens SET last_synced_at = %s WHERE provider = %s",
                (synced_at, provider),
            )

    def get_last_synced_at(self, provider: str) -> Optional[datetime]:
        with self._transaction(dict_rows=True) as (_, cur):
            cur.execute(
                "SELECT last_synced_at FROM oauth_tokens WHERE provider = %s",
                (provider,),
            )
            row = cur.fetchone()
            return row["last_synced_at"] if row else None

    @staticmethod
    def _calculate_rank(meetings_booked: int) -> str:
        rank_map = {
            0: "Iron",
            1: "Bronze",
            2: "Silver",
            3: "Gold",
            4: "Platinum",
            5: "Emerald",
            6: "Diamond",
            7: "Master",
            8: "Grandmaster",
        }
        if meetings_booked >= 9:
            return "Challenger"
        return rank_map.get(meetings_booked, "Iron")


def get_db() -> DatabaseQueries:
    return DatabaseQueries()

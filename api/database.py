"""PostgreSQL connection pool for the API (health checks)."""

import logging
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from api.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    def __init__(self, min_connections: int = 1, max_connections: int = 10):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool = None
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        self._pool = psycopg2.pool.SimpleConnectionPool(
            self.min_connections,
            self.max_connections,
            settings.DATABASE_URL,
            cursor_factory=RealDictCursor,
        )
        logger.info(
            "Database connection pool initialized (min=%s, max=%s)",
            self.min_connections,
            self.max_connections,
        )

    def get_connection(self):
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        conn = self._pool.getconn()
        if conn is None:
            raise RuntimeError("Connection pool exhausted")
        return conn

    def return_connection(self, conn) -> None:
        if self._pool is not None and conn is not None:
            self._pool.putconn(conn)

    def close_all_connections(self) -> None:
        if self._pool is not None:
            self._pool.closeall()
            logger.info("All database connections closed")

    @contextmanager
    def get_cursor(self) -> Generator:
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error("Database error: %s", e)
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)


db_pool = DatabaseConnectionPool(min_connections=2, max_connections=10)


async def check_database_health() -> bool:
    try:
        with db_pool.get_cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            return result is not None
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return False


def cleanup_database_connections() -> None:
    db_pool.close_all_connections()

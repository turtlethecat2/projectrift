"""
Database connection management for Project Rift API
Handles connection pooling and session management
"""

import logging
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from api.config import settings

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """Manages PostgreSQL connection pool"""

    def __init__(self, min_connections: int = 1, max_connections: int = 10):
        """
        Initialize connection pool

        Args:
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
        """
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool = None
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Create the connection pool"""
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                settings.DATABASE_URL,
                cursor_factory=RealDictCursor,
            )
            logger.info(
                f"Database connection pool initialized "
                f"(min={self.min_connections}, max={self.max_connections})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    def get_connection(self):
        """
        Get a connection from the pool

        Returns:
            Database connection

        Raises:
            Exception if pool is exhausted
        """
        if self._pool is None:
            raise Exception("Connection pool not initialized")

        try:
            conn = self._pool.getconn()
            if conn is None:
                raise Exception("Connection pool exhausted")
            return conn
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    def return_connection(self, conn) -> None:
        """
        Return a connection to the pool

        Args:
            conn: Database connection to return
        """
        if self._pool is not None and conn is not None:
            self._pool.putconn(conn)

    def close_all_connections(self) -> None:
        """Close all connections in the pool"""
        if self._pool is not None:
            self._pool.closeall()
            logger.info("All database connections closed")

    @contextmanager
    def get_cursor(self) -> Generator:
        """
        Context manager for database cursor

        Yields:
            Database cursor with automatic connection management

        Example:
            with db_pool.get_cursor() as cur:
                cur.execute("SELECT * FROM users")
                results = cur.fetchall()
        """
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
            logger.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)


# Global connection pool instance
db_pool = DatabaseConnectionPool(min_connections=2, max_connections=10)


def get_db_pool() -> DatabaseConnectionPool:
    """
    Get the global database connection pool

    Returns:
        DatabaseConnectionPool instance
    """
    return db_pool


async def check_database_health() -> bool:
    """
    Check if database is accessible

    Returns:
        True if database is healthy, False otherwise
    """
    try:
        with db_pool.get_cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            return result is not None
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Cleanup function to be called on application shutdown
def cleanup_database_connections() -> None:
    """Close all database connections on shutdown"""
    db_pool.close_all_connections()

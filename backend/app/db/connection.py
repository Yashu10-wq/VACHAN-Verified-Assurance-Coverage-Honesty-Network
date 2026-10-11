"""
PostgreSQL connectivity layer utilizing Psycopg 3 and Neon Cloud PostgreSQL.
Strictly prohibits SQLite and SQLAlchemy.
All queries use pure parameterized SQL and transactional guarantees.
"""

from contextlib import asynccontextmanager
import sys
from typing import AsyncGenerator, Optional
import psycopg
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

# Ensure Windows asyncio compatibility with psycopg 3
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.config import get_settings
from app.core.exceptions import DatabaseException
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global connection pool instance
_pool: Optional[AsyncConnectionPool] = None


def create_connection_pool() -> AsyncConnectionPool:
    """Creates a configured AsyncConnectionPool for Neon Cloud PostgreSQL."""
    settings = get_settings()
    conn_string = settings.get_database_url()

    logger.info(
        "Initializing Neon PostgreSQL connection pool (host: %s)",
        settings.get_sanitized_database_host(),
    )

    return AsyncConnectionPool(
        conninfo=conn_string,
        min_size=1,
        max_size=10,
        timeout=float(settings.DATABASE_CONNECT_TIMEOUT),
        max_idle=300.0,
        open=False,  # Opened explicitly on application startup
    )


async def init_db_pool() -> AsyncConnectionPool:
    """Initializes and opens the database connection pool."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = create_connection_pool()
    try:
        await _pool.open(wait=True, timeout=float(get_settings().DATABASE_CONNECT_TIMEOUT))
        logger.info("Neon PostgreSQL connection pool opened successfully.")
    except Exception as exc:
        logger.error("Failed to open Neon PostgreSQL connection pool: %s", type(exc).__name__)
        # Pool remains available to retry on subsequent calls
    return _pool


async def close_db_pool() -> None:
    """Closes the global database connection pool gracefully."""
    global _pool
    if _pool is not None:
        if not _pool.closed:
            logger.info("Closing Neon PostgreSQL connection pool.")
            await _pool.close()
        _pool = None


def get_db_pool() -> AsyncConnectionPool:
    """Returns the active pool, creating a fresh one if closed or uninitialized."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = create_connection_pool()
    return _pool


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Context manager yielding an AsyncConnection from the pool.
    Ensures safe return to pool and converts internal driver errors to sanitized DatabaseExceptions.
    """
    global _pool
    if _pool is None or _pool.closed:
        _pool = create_connection_pool()
    pool = _pool
    if pool.closed:
        try:
            await pool.open(wait=True, timeout=float(get_settings().DATABASE_CONNECT_TIMEOUT))
        except Exception as exc:
            raise DatabaseException(f"Database connection pool unavailable: {type(exc).__name__}") from exc

    try:
        async with pool.connection() as conn:
            yield conn
    except psycopg.OperationalError as exc:
        logger.error("Database operational error encountered: %s", type(exc).__name__)
        raise DatabaseException("Database service is currently unreachable.") from exc
    except psycopg.Error as exc:
        logger.error("Database query error encountered: %s", type(exc).__name__)
        raise DatabaseException("Database operation failed.") from exc


async def check_database_readiness(timeout_seconds: float = 3.0) -> bool:
    """
    Checks actual Neon PostgreSQL database readiness by executing 'SELECT 1'.
    Returns True if healthy; raises DatabaseException or returns False if unreachable.
    """
    settings = get_settings()
    conn_string = settings.get_database_url()

    try:
        # Establish direct async connection with strict timeout
        async with await psycopg.AsyncConnection.connect(
            conn_string,
            connect_timeout=int(timeout_seconds),
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1;")
                row = await cur.fetchone()
                return bool(row and row[0] == 1)
    except psycopg.OperationalError as exc:
        logger.warning("Database readiness check failed (operational): %s", type(exc).__name__)
        raise DatabaseException("Neon Cloud PostgreSQL is unreachable.") from exc
    except Exception as exc:
        logger.warning("Database readiness check failed: %s", type(exc).__name__)
        raise DatabaseException(f"Database readiness check failed: {type(exc).__name__}") from exc

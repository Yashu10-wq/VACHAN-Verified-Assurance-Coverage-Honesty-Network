"""
Token and session data access repository using Psycopg 3 parameterized SQL.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import psycopg

from app.core.exceptions import DatabaseException


async def create_user_token(
    conn: psycopg.AsyncConnection,
    user_id: str,
    token_type: str,
    token_hash: str,
    expires_at: datetime,
) -> Dict[str, Any]:
    """Stores a single-use token hash."""
    sql = """
    INSERT INTO user_tokens (user_id, token_type, token_hash, expires_at)
    VALUES (%s, %s, %s, %s)
    RETURNING id, user_id, token_type, token_hash, expires_at, used_at, created_at;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (user_id, token_type, token_hash, expires_at))
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to insert user token.")
        return {
            "id": str(row[0]),
            "user_id": str(row[1]),
            "token_type": row[2],
            "token_hash": row[3],
            "expires_at": row[4],
            "used_at": row[5],
            "created_at": row[6],
        }


async def get_valid_user_token(
    conn: psycopg.AsyncConnection,
    token_type: str,
    token_hash: str,
) -> Optional[Dict[str, Any]]:
    """Retrieves an unexpired, unused token by hash."""
    sql = """
    SELECT id, user_id, token_type, token_hash, expires_at, used_at, created_at
    FROM user_tokens
    WHERE token_type = %s
      AND token_hash = %s
      AND used_at IS NULL
      AND expires_at > CURRENT_TIMESTAMP;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (token_type, token_hash))
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "id": str(row[0]),
            "user_id": str(row[1]),
            "token_type": row[2],
            "token_hash": row[3],
            "expires_at": row[4],
            "used_at": row[5],
            "created_at": row[6],
        }


async def mark_token_used(conn: psycopg.AsyncConnection, token_id: str) -> None:
    """Marks a single-use token as consumed."""
    sql = "UPDATE user_tokens SET used_at = CURRENT_TIMESTAMP WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (token_id,))


async def create_refresh_token(
    conn: psycopg.AsyncConnection,
    user_id: str,
    token_hash: str,
    expires_at: datetime,
) -> None:
    """Stores a refresh token hash for session management."""
    sql = """
    INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
    VALUES (%s, %s, %s);
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (user_id, token_hash, expires_at))


async def get_valid_refresh_token(
    conn: psycopg.AsyncConnection,
    token_hash: str,
) -> Optional[Dict[str, Any]]:
    """Retrieves an active, unrevoked refresh token."""
    sql = """
    SELECT id, user_id, token_hash, expires_at, revoked_at, created_at
    FROM refresh_tokens
    WHERE token_hash = %s
      AND revoked_at IS NULL
      AND expires_at > CURRENT_TIMESTAMP;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (token_hash,))
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "id": str(row[0]),
            "user_id": str(row[1]),
            "token_hash": row[2],
            "expires_at": row[3],
            "revoked_at": row[4],
            "created_at": row[5],
        }


async def revoke_refresh_token(conn: psycopg.AsyncConnection, token_hash: str) -> None:
    """Revokes a specific refresh token."""
    sql = "UPDATE refresh_tokens SET revoked_at = CURRENT_TIMESTAMP WHERE token_hash = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (token_hash,))


async def revoke_all_user_refresh_tokens(conn: psycopg.AsyncConnection, user_id: str) -> None:
    """Revokes all active refresh tokens for a user (logout all devices)."""
    sql = "UPDATE refresh_tokens SET revoked_at = CURRENT_TIMESTAMP WHERE user_id = %s AND revoked_at IS NULL;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (user_id,))

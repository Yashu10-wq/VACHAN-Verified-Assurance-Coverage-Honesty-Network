"""
User and identity data access repository using Psycopg 3 pure parameterized SQL.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
import psycopg

from app.core.exceptions import DatabaseException


def _row_to_user_dict(row: tuple) -> Dict[str, Any]:
    """Converts a database row into a structured user dict."""
    return {
        "id": str(row[0]),
        "email": row[1],
        "password_hash": row[2],
        "full_name": row[3],
        "phone": row[4],
        "role": row[5],
        "account_status": row[6],
        "email_verified_at": row[7].isoformat() if row[7] else None,
        "approved_by": str(row[8]) if row[8] else None,
        "approved_at": row[9].isoformat() if row[9] else None,
        "rejection_reason": row[10],
        "created_at": row[11].isoformat() if row[11] else None,
        "updated_at": row[12].isoformat() if row[12] else None,
        "last_login_at": row[13].isoformat() if row[13] else None,
    }


USER_SELECT_FIELDS = """
    id, email, password_hash, full_name, phone, role, account_status,
    email_verified_at, approved_by, approved_at, rejection_reason,
    created_at, updated_at, last_login_at
"""


async def get_user_by_id(conn: psycopg.AsyncConnection, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by UUID."""
    sql = f"SELECT {USER_SELECT_FIELDS} FROM users WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (user_id,))
        row = await cur.fetchone()
        return _row_to_user_dict(row) if row else None


async def get_user_by_email(conn: psycopg.AsyncConnection, email: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by normalized email."""
    sql = f"SELECT {USER_SELECT_FIELDS} FROM users WHERE LOWER(email) = LOWER(%s);"
    async with conn.cursor() as cur:
        await cur.execute(sql, (email.strip(),))
        row = await cur.fetchone()
        return _row_to_user_dict(row) if row else None


async def create_user(
    conn: psycopg.AsyncConnection,
    email: str,
    password_hash: str,
    full_name: str,
    role: str,
    account_status: str,
    phone: Optional[str] = None,
) -> Dict[str, Any]:
    """Creates a new user account with parameterized SQL."""
    sql = f"""
    INSERT INTO users (email, password_hash, full_name, phone, role, account_status)
    VALUES (LOWER(%s), %s, %s, %s, %s, %s)
    RETURNING {USER_SELECT_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (email.strip(), password_hash, full_name.strip(), phone, role, account_status),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to insert user.")
        return _row_to_user_dict(row)


async def update_last_login(conn: psycopg.AsyncConnection, user_id: str) -> None:
    """Updates user last_login_at timestamp."""
    sql = "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (user_id,))


async def verify_user_email(conn: psycopg.AsyncConnection, user_id: str) -> None:
    """Marks email as verified and activates account if pending verification."""
    sql = """
    UPDATE users
    SET email_verified_at = CURRENT_TIMESTAMP,
        account_status = CASE
            WHEN account_status = 'PENDING_VERIFICATION' THEN 'ACTIVE'
            ELSE account_status
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (user_id,))


async def update_password(
    conn: psycopg.AsyncConnection, user_id: str, new_password_hash: str
) -> None:
    """Updates password hash securely."""
    sql = """
    UPDATE users
    SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
    WHERE id = %s;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (new_password_hash, user_id))


async def update_account_status(
    conn: psycopg.AsyncConnection,
    user_id: str,
    new_status: str,
    approved_by: Optional[str] = None,
    rejection_reason: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Updates account authorization status (ACTIVE, REJECTED, SUSPENDED, etc.)."""
    sql = f"""
    UPDATE users
    SET account_status = %s,
        approved_by = %s,
        approved_at = CASE WHEN %s = 'ACTIVE' THEN CURRENT_TIMESTAMP ELSE approved_at END,
        rejection_reason = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {USER_SELECT_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql, (new_status, approved_by, new_status, rejection_reason, user_id)
        )
        row = await cur.fetchone()
        return _row_to_user_dict(row) if row else None


async def list_users(
    conn: psycopg.AsyncConnection,
    role: Optional[str] = None,
    account_status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Lists users with optional role and status filters."""
    query = f"SELECT {USER_SELECT_FIELDS} FROM users WHERE 1=1"
    params: List[Any] = []
    if role:
        query += " AND role = %s"
        params.append(role)
    if account_status:
        query += " AND account_status = %s"
        params.append(account_status)
    query += " ORDER BY created_at DESC LIMIT %s;"
    params.append(limit)

    async with conn.cursor() as cur:
        await cur.execute(query, tuple(params))
        rows = await cur.fetchall()
        return [_row_to_user_dict(r) for r in rows]

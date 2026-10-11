"""
Policy catalogue and versioning repository using Psycopg 3 parameterized SQL.
"""

from datetime import date
from decimal import Decimal
import json
from typing import Any, Dict, List, Optional
import psycopg

from app.core.exceptions import DatabaseException


def _row_to_policy_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "insurer_name": row[1],
        "policy_name": row[2],
        "policy_code": row[3],
        "category": row[4],
        "description": row[5],
        "coverage_limit": float(row[6]),
        "waiting_period_days": row[7],
        "claim_filing_window_days": row[8],
        "is_active": row[9],
        "created_by": str(row[10]) if row[10] else None,
        "created_at": row[11].isoformat() if row[11] else None,
        "updated_at": row[12].isoformat() if row[12] else None,
    }


def _row_to_version_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "policy_id": str(row[1]),
        "version_number": row[2],
        "document_storage_ref": row[3],
        "document_checksum": row[4],
        "effective_date": row[5].isoformat() if isinstance(row[5], date) else str(row[5]),
        "expiry_date": row[6].isoformat() if row[6] and isinstance(row[6], date) else (str(row[6]) if row[6] else None),
        "terms_json": row[7] if isinstance(row[7], dict) else json.loads(row[7] or "{}"),
        "is_published": row[8],
        "published_at": row[9].isoformat() if row[9] else None,
        "published_by": str(row[10]) if row[10] else None,
        "created_at": row[11].isoformat() if row[11] else None,
    }


POLICY_FIELDS = """
    id, insurer_name, policy_name, policy_code, category, description,
    coverage_limit, waiting_period_days, claim_filing_window_days,
    is_active, created_by, created_at, updated_at
"""

VERSION_FIELDS = """
    id, policy_id, version_number, document_storage_ref, document_checksum,
    effective_date, expiry_date, terms_json, is_published,
    published_at, published_by, created_at
"""


async def create_policy(
    conn: psycopg.AsyncConnection,
    insurer_name: str,
    policy_name: str,
    policy_code: str,
    category: str,
    description: str,
    coverage_limit: Decimal,
    waiting_period_days: int = 0,
    claim_filing_window_days: int = 30,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Creates a master insurance policy record."""
    sql = f"""
    INSERT INTO policies (
        insurer_name, policy_name, policy_code, category, description,
        coverage_limit, waiting_period_days, claim_filing_window_days, created_by
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING {POLICY_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                insurer_name.strip(),
                policy_name.strip(),
                policy_code.strip().upper(),
                category,
                description.strip(),
                coverage_limit,
                waiting_period_days,
                claim_filing_window_days,
                created_by,
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to insert policy.")
        return _row_to_policy_dict(row)


async def get_policy_by_id(conn: psycopg.AsyncConnection, policy_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves policy by UUID."""
    sql = f"SELECT {POLICY_FIELDS} FROM policies WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (policy_id,))
        row = await cur.fetchone()
        return _row_to_policy_dict(row) if row else None


async def get_policy_by_code(conn: psycopg.AsyncConnection, policy_code: str) -> Optional[Dict[str, Any]]:
    """Retrieves policy by unique policy code."""
    sql = f"SELECT {POLICY_FIELDS} FROM policies WHERE UPPER(policy_code) = UPPER(%s);"
    async with conn.cursor() as cur:
        await cur.execute(sql, (policy_code.strip(),))
        row = await cur.fetchone()
        return _row_to_policy_dict(row) if row else None


async def list_policies(
    conn: psycopg.AsyncConnection,
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
) -> List[Dict[str, Any]]:
    """Lists insurance policies with optional filters."""
    query = f"SELECT {POLICY_FIELDS} FROM policies WHERE 1=1"
    params: List[Any] = []
    if category:
        query += " AND category = %s"
        params.append(category)
    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)
    query += " ORDER BY policy_name ASC;"

    async with conn.cursor() as cur:
        await cur.execute(query, tuple(params))
        rows = await cur.fetchall()
        return [_row_to_policy_dict(r) for r in rows]


async def create_policy_version(
    conn: psycopg.AsyncConnection,
    policy_id: str,
    version_number: int,
    document_storage_ref: str,
    document_checksum: str,
    effective_date: date,
    expiry_date: Optional[date] = None,
    terms_json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Creates a new immutable policy version."""
    sql = f"""
    INSERT INTO policy_versions (
        policy_id, version_number, document_storage_ref, document_checksum,
        effective_date, expiry_date, terms_json
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING {VERSION_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                policy_id,
                version_number,
                document_storage_ref.strip(),
                document_checksum.strip(),
                effective_date,
                expiry_date,
                json.dumps(terms_json or {}),
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to insert policy version.")
        return _row_to_version_dict(row)


async def publish_policy_version(
    conn: psycopg.AsyncConnection, version_id: str, published_by: str
) -> Optional[Dict[str, Any]]:
    """Publishes a policy version making it eligible for customer registration."""
    sql = f"""
    UPDATE policy_versions
    SET is_published = TRUE,
        published_at = CURRENT_TIMESTAMP,
        published_by = %s
    WHERE id = %s
    RETURNING {VERSION_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (published_by, version_id))
        row = await cur.fetchone()
        return _row_to_version_dict(row) if row else None


async def get_published_version(
    conn: psycopg.AsyncConnection, policy_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieves the latest published version of a policy."""
    sql = f"""
    SELECT {VERSION_FIELDS}
    FROM policy_versions
    WHERE policy_id = %s AND is_published = TRUE
    ORDER BY version_number DESC
    LIMIT 1;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (policy_id,))
        row = await cur.fetchone()
        return _row_to_version_dict(row) if row else None


async def get_policy_version_by_id(
    conn: psycopg.AsyncConnection, version_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieves a specific policy version by UUID."""
    sql = f"SELECT {VERSION_FIELDS} FROM policy_versions WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (version_id,))
        row = await cur.fetchone()
        return _row_to_version_dict(row) if row else None


async def list_policy_versions(
    conn: psycopg.AsyncConnection, policy_id: str
) -> List[Dict[str, Any]]:
    """Lists all versions for a given policy."""
    sql = f"""
    SELECT {VERSION_FIELDS}
    FROM policy_versions
    WHERE policy_id = %s
    ORDER BY version_number DESC;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (policy_id,))
        rows = await cur.fetchall()
        return [_row_to_version_dict(r) for r in rows]

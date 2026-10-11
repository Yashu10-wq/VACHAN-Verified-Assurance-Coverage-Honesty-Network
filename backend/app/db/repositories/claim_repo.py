"""
Claims database repository using Psycopg 3 parameterized SQL.
Provides atomic transactions, row-level locking for status transitions,
and scoped queries for customer, agent, and authority access.
"""

from datetime import date
from decimal import Decimal
import json
from typing import Any, Dict, List, Optional, Tuple
import psycopg

from app.core.exceptions import DatabaseException


def _row_to_claim_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "customer_id": str(row[1]),
        "registration_id": str(row[2]),
        "policy_id": str(row[3]),
        "policy_version_id": str(row[4]),
        "claim_category": row[5],
        "requested_amount": str(row[6]),
        "incident_date": row[7].isoformat() if isinstance(row[7], date) else str(row[7]),
        "submission_timestamp": row[8].isoformat() if row[8] else None,
        "description": row[9],
        "structured_details": row[10] if isinstance(row[10], dict) else json.loads(row[10] or "{}"),
        "status": row[11],
        "created_at": row[12].isoformat() if row[12] else None,
        "updated_at": row[13].isoformat() if row[13] else None,
    }


def _row_to_history_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "claim_id": str(row[1]),
        "actor_id": str(row[2]) if row[2] else None,
        "actor_role": row[3],
        "previous_status": row[4],
        "new_status": row[5],
        "reason": row[6],
        "decision_metadata": row[7] if isinstance(row[7], dict) else json.loads(row[7] or "{}"),
        "audit_correlation_id": row[8],
        "created_at": row[9].isoformat() if row[9] else None,
    }


CLAIM_FIELDS = """
    id, customer_id, registration_id, policy_id, policy_version_id,
    claim_category, requested_amount, incident_date, submission_timestamp,
    description, structured_details, status, created_at, updated_at
"""

HISTORY_FIELDS = """
    id, claim_id, actor_id, actor_role, previous_status, new_status,
    reason, decision_metadata, audit_correlation_id, created_at
"""


async def create_claim(
    conn: psycopg.AsyncConnection,
    customer_id: str,
    registration_id: str,
    policy_id: str,
    policy_version_id: str,
    claim_category: str,
    requested_amount: Decimal,
    incident_date: date,
    description: str,
    structured_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Creates a new insurance claim with initial SUBMITTED status."""
    sql = f"""
    INSERT INTO claims (
        customer_id, registration_id, policy_id, policy_version_id,
        claim_category, requested_amount, incident_date, description,
        structured_details, status
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'SUBMITTED')
    RETURNING {CLAIM_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                customer_id,
                registration_id,
                policy_id,
                policy_version_id,
                claim_category,
                requested_amount,
                incident_date,
                description.strip(),
                json.dumps(structured_details or {}),
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to insert claim record.")
        return _row_to_claim_dict(row)


async def get_claim_by_id(
    conn: psycopg.AsyncConnection, claim_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieves a single claim by UUID."""
    sql = f"SELECT {CLAIM_FIELDS} FROM claims WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (claim_id,))
        row = await cur.fetchone()
        return _row_to_claim_dict(row) if row else None


async def list_claims(
    conn: psycopg.AsyncConnection,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Lists claims scoped by permissions:
    - Customer: restricted to customer_id.
    - Agent: restricted to registrations initiated by agent_id.
    - Authority: system-wide or filtered by status.
    """
    params: List[Any] = []
    if agent_id:
        query = f"""
        SELECT c.id, c.customer_id, c.registration_id, c.policy_id, c.policy_version_id,
               c.claim_category, c.requested_amount, c.incident_date, c.submission_timestamp,
               c.description, c.structured_details, c.status, c.created_at, c.updated_at
        FROM claims c
        INNER JOIN policy_registrations pr ON pr.id = c.registration_id
        WHERE pr.agent_id = %s
        """
        params.append(agent_id)
        if status:
            query += " AND c.status = %s"
            params.append(status)
        query += " ORDER BY c.created_at DESC LIMIT %s OFFSET %s;"
        params.extend([limit, offset])
    else:
        query = f"SELECT {CLAIM_FIELDS} FROM claims WHERE 1=1"
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
        if status:
            query += " AND status = %s"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s;"
        params.extend([limit, offset])

    async with conn.cursor() as cur:
        await cur.execute(query, tuple(params))
        rows = await cur.fetchall()
        return [_row_to_claim_dict(r) for r in rows]


async def count_claims(
    conn: psycopg.AsyncConnection,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    """Counts total claims matching scope filters."""
    params: List[Any] = []
    if agent_id:
        query = """
        SELECT COUNT(*)
        FROM claims c
        INNER JOIN policy_registrations pr ON pr.id = c.registration_id
        WHERE pr.agent_id = %s
        """
        params.append(agent_id)
        if status:
            query += " AND c.status = %s"
            params.append(status)
    else:
        query = "SELECT COUNT(*) FROM claims WHERE 1=1"
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
        if status:
            query += " AND status = %s"
            params.append(status)

    async with conn.cursor() as cur:
        await cur.execute(query, tuple(params))
        row = await cur.fetchone()
        return row[0] if row else 0


async def update_claim_status_atomic(
    conn: psycopg.AsyncConnection,
    claim_id: str,
    new_status: str,
    actor_id: Optional[str],
    actor_role: str,
    reason: str,
    decision_metadata: Optional[Dict[str, Any]] = None,
    audit_correlation_id: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Acquires row-level lock (FOR UPDATE), updates status, and inserts audit history.
    Returns (previous_status, updated_claim_dict).
    """
    lock_sql = "SELECT status FROM claims WHERE id = %s FOR UPDATE;"
    update_sql = f"""
    UPDATE claims
    SET status = %s, updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {CLAIM_FIELDS};
    """
    history_sql = """
    INSERT INTO claim_status_history (
        claim_id, actor_id, actor_role, previous_status,
        new_status, reason, decision_metadata, audit_correlation_id
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """

    async with conn.cursor() as cur:
        await cur.execute(lock_sql, (claim_id,))
        lock_row = await cur.fetchone()
        if not lock_row:
            raise DatabaseException(f"Claim with ID {claim_id} not found for status update.")
        previous_status = lock_row[0]

        await cur.execute(update_sql, (new_status, claim_id))
        updated_row = await cur.fetchone()
        if not updated_row:
            raise DatabaseException("Failed to update claim status.")

        json_metadata = json.dumps(decision_metadata or {})
        await cur.execute(
            history_sql,
            (
                claim_id,
                actor_id,
                actor_role,
                previous_status,
                new_status,
                reason.strip(),
                json_metadata,
                audit_correlation_id,
            ),
        )

        return previous_status, _row_to_claim_dict(updated_row)


async def get_claim_history(
    conn: psycopg.AsyncConnection, claim_id: str
) -> List[Dict[str, Any]]:
    """Retrieves full audit trail of lifecycle status transitions for a claim."""
    sql = f"""
    SELECT {HISTORY_FIELDS}
    FROM claim_status_history
    WHERE claim_id = %s
    ORDER BY created_at ASC;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (claim_id,))
        rows = await cur.fetchall()
        return [_row_to_history_dict(r) for r in rows]

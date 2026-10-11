"""
Policy registration repository using Psycopg 3 parameterized SQL.
Enforces customer-gated confirmation, agent scoping, and lifecycle state tracking.
"""

from typing import Any, Dict, List, Optional
import psycopg

from app.core.exceptions import DatabaseException


def _row_to_reg_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "customer_id": str(row[1]),
        "agent_id": str(row[2]),
        "policy_id": str(row[3]),
        "policy_version_id": str(row[4]),
        "status": row[5],
        "customer_consent": row[6],
        "consent_timestamp": row[7].isoformat() if row[7] else None,
        "consent_notes": row[8],
        "customer_decision_at": row[9].isoformat() if row[9] else None,
        "activated_at": row[10].isoformat() if row[10] else None,
        "declined_at": row[11].isoformat() if row[11] else None,
        "cancelled_at": row[12].isoformat() if row[12] else None,
        "created_at": row[13].isoformat() if row[13] else None,
        "updated_at": row[14].isoformat() if row[14] else None,
    }


REG_FIELDS = """
    id, customer_id, agent_id, policy_id, policy_version_id,
    status, customer_consent, consent_timestamp, consent_notes,
    customer_decision_at, activated_at, declined_at, cancelled_at,
    created_at, updated_at
"""


async def create_registration(
    conn: psycopg.AsyncConnection,
    customer_id: str,
    agent_id: str,
    policy_id: str,
    policy_version_id: str,
    customer_consent: bool = True,
    consent_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Creates a new policy registration in PENDING_VERIFICATION state."""
    sql = f"""
    INSERT INTO policy_registrations (
        customer_id, agent_id, policy_id, policy_version_id,
        customer_consent, consent_timestamp, consent_notes, status
    )
    VALUES (%s, %s, %s, %s, %s, CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END, %s, 'PENDING_VERIFICATION')
    RETURNING {REG_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                customer_id,
                agent_id,
                policy_id,
                policy_version_id,
                customer_consent,
                customer_consent,
                consent_notes,
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to insert policy registration.")
        return _row_to_reg_dict(row)


async def get_registration_by_id(
    conn: psycopg.AsyncConnection, registration_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieves a registration by UUID."""
    sql = f"SELECT {REG_FIELDS} FROM policy_registrations WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (registration_id,))
        row = await cur.fetchone()
        return _row_to_reg_dict(row) if row else None


async def list_registrations(
    conn: psycopg.AsyncConnection,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Lists registrations scoped to customer, agent, or status."""
    query = f"SELECT {REG_FIELDS} FROM policy_registrations WHERE 1=1"
    params: List[Any] = []
    if customer_id:
        query += " AND customer_id = %s"
        params.append(customer_id)
    if agent_id:
        query += " AND agent_id = %s"
        params.append(agent_id)
    if status:
        query += " AND status = %s"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT %s;"
    params.append(limit)

    async with conn.cursor() as cur:
        await cur.execute(query, tuple(params))
        rows = await cur.fetchall()
        return [_row_to_reg_dict(r) for r in rows]


async def update_registration_status(
    conn: psycopg.AsyncConnection,
    registration_id: str,
    new_status: str,
) -> Optional[Dict[str, Any]]:
    """Updates registration lifecycle state."""
    sql = f"""
    UPDATE policy_registrations
    SET status = %s, updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {REG_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (new_status, registration_id))
        row = await cur.fetchone()
        return _row_to_reg_dict(row) if row else None


async def confirm_registration(
    conn: psycopg.AsyncConnection,
    registration_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Explicitly activates a policy registration upon customer affirmative confirmation.
    Transitions status to CONFIRMED and records decision timestamp.
    """
    sql = f"""
    UPDATE policy_registrations
    SET status = 'CONFIRMED',
        customer_decision_at = CURRENT_TIMESTAMP,
        activated_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {REG_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (registration_id,))
        row = await cur.fetchone()
        return _row_to_reg_dict(row) if row else None


async def decline_registration(
    conn: psycopg.AsyncConnection,
    registration_id: str,
) -> Optional[Dict[str, Any]]:
    """Records customer decision to decline the proposed policy registration."""
    sql = f"""
    UPDATE policy_registrations
    SET status = 'DECLINED',
        customer_decision_at = CURRENT_TIMESTAMP,
        declined_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {REG_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (registration_id,))
        row = await cur.fetchone()
        return _row_to_reg_dict(row) if row else None

"""
Audit logging repository using Psycopg 3 parameterized SQL.
Integrates tamper-evident cryptographic hash-chaining on all audit events.
"""

from typing import Any, Dict, List, Optional
import psycopg

from app.services.audit_chain import append_chained_audit_event


async def log_audit_event(
    conn: psycopg.AsyncConnection,
    actor_id: Optional[str],
    actor_role: Optional[str],
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Inserts a structured security audit event deterministically chained into the audit hash sequence."""
    return await append_chained_audit_event(
        conn=conn,
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata,
    )


async def get_audit_event_by_id(
    conn: psycopg.AsyncConnection,
    event_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieves an audit event by UUID."""
    sql = """
    SELECT id, actor_id, actor_role, action, target_type, target_id, metadata,
           sequence_number, payload_hash, previous_hash, event_hash,
           hash_version, anchoring_status, batch_id, created_at
    FROM audit_logs
    WHERE id = %s;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (event_id,))
        row = await cur.fetchone()
        if not row:
            return None
        return {
            "id": str(row[0]),
            "actor_id": str(row[1]) if row[1] else None,
            "actor_role": row[2],
            "action": row[3],
            "target_type": row[4],
            "target_id": str(row[5]) if row[5] else None,
            "metadata": row[6] if isinstance(row[6], dict) else {},
            "sequence_number": row[7],
            "payload_hash": row[8],
            "previous_hash": row[9],
            "event_hash": row[10],
            "hash_version": row[11],
            "anchoring_status": row[12],
            "batch_id": str(row[13]) if row[13] else None,
            "created_at": row[14].isoformat() if row[14] else None,
        }

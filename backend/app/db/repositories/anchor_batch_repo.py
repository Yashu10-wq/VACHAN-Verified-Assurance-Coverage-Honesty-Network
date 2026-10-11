"""
Audit Anchor Batches repository using Psycopg 3 parameterized SQL.
Manages Merkle batch creation, event assignment, transaction receipts, and query scopes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import psycopg

from app.core.exceptions import DatabaseException


BATCH_FIELDS = """
    id, batch_sequence, batch_root_hash, first_sequence_number, last_sequence_number,
    event_count, status, tx_hash, block_number, chain_id, contract_address,
    anchored_at, error_message, created_at, updated_at
"""


def _row_to_batch_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "batch_sequence": row[1],
        "batch_root_hash": row[2],
        "first_sequence_number": row[3],
        "last_sequence_number": row[4],
        "event_count": row[5],
        "status": row[6],
        "tx_hash": row[7],
        "block_number": row[8],
        "chain_id": row[9],
        "contract_address": row[10],
        "anchored_at": row[11].isoformat() if row[11] else None,
        "error_message": row[12],
        "created_at": row[13].isoformat() if row[13] else None,
        "updated_at": row[14].isoformat() if row[14] else None,
    }


async def get_next_batch_sequence(conn: psycopg.AsyncConnection) -> int:
    """Returns the next sequential batch_sequence number."""
    sql = "SELECT COALESCE(MAX(batch_sequence), 0) + 1 FROM audit_anchor_batches;"
    async with conn.cursor() as cur:
        await cur.execute(sql)
        row = await cur.fetchone()
        return row[0] if row else 1


async def get_pending_audit_events(
    conn: psycopg.AsyncConnection,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Retrieves eligible unbatched audit events in ascending sequence order.
    Excludes internal anchor administration actions to prevent recursive loops.
    """
    sql = """
    SELECT id, actor_id, actor_role, action, target_type, target_id, metadata,
           sequence_number, payload_hash, previous_hash, event_hash,
           hash_version, anchoring_status, batch_id, created_at
    FROM audit_logs
    WHERE sequence_number IS NOT NULL
      AND (anchoring_status = 'PENDING' OR anchoring_status = 'FAILED')
      AND batch_id IS NULL
      AND action NOT IN ('ANCHOR_AUDIT_BATCH', 'RETRY_ANCHOR_BATCH')
    ORDER BY sequence_number ASC
    LIMIT %s;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (limit,))
        rows = await cur.fetchall()
        return [
            {
                "id": str(r[0]),
                "actor_id": str(r[1]) if r[1] else None,
                "actor_role": r[2],
                "action": r[3],
                "target_type": r[4],
                "target_id": str(r[5]) if r[5] else None,
                "metadata": r[6] if isinstance(r[6], dict) else {},
                "sequence_number": r[7],
                "payload_hash": r[8],
                "previous_hash": r[9],
                "event_hash": r[10],
                "hash_version": r[11],
                "anchoring_status": r[12],
                "batch_id": str(r[13]) if r[13] else None,
                "created_at": r[14].isoformat() if r[14] else None,
            }
            for r in rows
        ]


async def create_anchor_batch(
    conn: psycopg.AsyncConnection,
    batch_root_hash: str,
    first_seq: int,
    last_seq: int,
    event_count: int,
    event_ids: List[str],
) -> Dict[str, Any]:
    """
    Creates an audit batch record and marks associated audit events as BATCHED.
    """
    next_batch_seq = await get_next_batch_sequence(conn)

    insert_sql = f"""
    INSERT INTO audit_anchor_batches (
        batch_sequence, batch_root_hash, first_sequence_number,
        last_sequence_number, event_count, status
    )
    VALUES (%s, %s, %s, %s, %s, 'SUBMITTING')
    RETURNING {BATCH_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            insert_sql,
            (
                next_batch_seq,
                batch_root_hash,
                first_seq,
                last_seq,
                event_count,
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to create audit anchor batch.")
        batch = _row_to_batch_dict(row)
        batch_id = batch["id"]

        # Link audit events to this batch
        if event_ids:
            update_events_sql = """
            UPDATE audit_logs
            SET batch_id = %s,
                anchoring_status = 'BATCHED'
            WHERE id = ANY(%s::uuid[]);
            """
            await cur.execute(update_events_sql, (batch_id, event_ids))

        return batch


async def update_batch_anchored(
    conn: psycopg.AsyncConnection,
    batch_id: str,
    tx_hash: str,
    block_number: int,
    chain_id: int,
    contract_address: str,
) -> Optional[Dict[str, Any]]:
    """
    Marks a batch and its associated audit events as ANCHORED with verified receipt metadata.
    """
    now = datetime.now(timezone.utc)
    sql = f"""
    UPDATE audit_anchor_batches
    SET status = 'ANCHORED',
        tx_hash = %s,
        block_number = %s,
        chain_id = %s,
        contract_address = %s,
        anchored_at = %s,
        error_message = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {BATCH_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                tx_hash,
                block_number,
                chain_id,
                contract_address,
                now,
                batch_id,
            ),
        )
        row = await cur.fetchone()
        if not row:
            return None

        # Update events in batch to ANCHORED
        await cur.execute(
            """
            UPDATE audit_logs
            SET anchoring_status = 'ANCHORED'
            WHERE batch_id = %s;
            """,
            (batch_id,),
        )
        return _row_to_batch_dict(row)


async def update_batch_failed(
    conn: psycopg.AsyncConnection,
    batch_id: str,
    error_message: str,
) -> Optional[Dict[str, Any]]:
    """Marks a batch as FAILED and sets associated audit events back to PENDING for retry."""
    sql = f"""
    UPDATE audit_anchor_batches
    SET status = 'FAILED',
        error_message = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {BATCH_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (error_message, batch_id))
        row = await cur.fetchone()
        if not row:
            return None

        # Release events back to PENDING so they can be re-evaluated
        await cur.execute(
            """
            UPDATE audit_logs
            SET anchoring_status = 'FAILED'
            WHERE batch_id = %s;
            """,
            (batch_id,),
        )
        return _row_to_batch_dict(row)


async def get_batch_by_id(
    conn: psycopg.AsyncConnection,
    batch_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieves batch by UUID."""
    sql = f"SELECT {BATCH_FIELDS} FROM audit_anchor_batches WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (batch_id,))
        row = await cur.fetchone()
        return _row_to_batch_dict(row) if row else None


async def get_events_for_batch(
    conn: psycopg.AsyncConnection,
    batch_id: str,
) -> List[Dict[str, Any]]:
    """Retrieves all audit events included in a batch ordered by sequence number."""
    sql = """
    SELECT id, actor_id, actor_role, action, target_type, target_id, metadata,
           sequence_number, payload_hash, previous_hash, event_hash,
           hash_version, anchoring_status, batch_id, created_at
    FROM audit_logs
    WHERE batch_id = %s
    ORDER BY sequence_number ASC;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (batch_id,))
        rows = await cur.fetchall()
        return [
            {
                "id": str(r[0]),
                "actor_id": str(r[1]) if r[1] else None,
                "actor_role": r[2],
                "action": r[3],
                "target_type": r[4],
                "target_id": str(r[5]) if r[5] else None,
                "metadata": r[6] if isinstance(r[6], dict) else {},
                "sequence_number": r[7],
                "payload_hash": r[8],
                "previous_hash": r[9],
                "event_hash": r[10],
                "hash_version": r[11],
                "anchoring_status": r[12],
                "batch_id": str(r[13]) if r[13] else None,
                "created_at": r[14].isoformat() if r[14] else None,
            }
            for r in rows
        ]


async def get_anchoring_counts(conn: psycopg.AsyncConnection) -> Dict[str, int]:
    """Retrieves count of events across anchoring statuses."""
    sql = """
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE sequence_number IS NULL) AS unchained,
        COUNT(*) FILTER (WHERE anchoring_status = 'PENDING') AS pending,
        COUNT(*) FILTER (WHERE anchoring_status = 'BATCHED') AS batched,
        COUNT(*) FILTER (WHERE anchoring_status = 'ANCHORED') AS anchored,
        COUNT(*) FILTER (WHERE anchoring_status = 'FAILED') AS failed
    FROM audit_logs;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql)
        row = await cur.fetchone()
        return {
            "total_events": row[0] or 0,
            "unchained_events": row[1] or 0,
            "pending_events": row[2] or 0,
            "batched_events": row[3] or 0,
            "anchored_events": row[4] or 0,
            "failed_events": row[5] or 0,
        }

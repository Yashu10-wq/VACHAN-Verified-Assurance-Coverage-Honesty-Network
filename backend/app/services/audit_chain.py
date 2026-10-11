"""
Tamper-Evident Audit Hash Chain Engine for InsureChain VoiceGuard.
Enforces deterministic canonical JSON serialization, SHA-256 cryptographic linkage,
PostgreSQL advisory transaction locks for concurrent serialization,
and non-destructive baseline backfills for historical records.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
import psycopg

from app.core.exceptions import DatabaseException, ValidationException
from app.core.logging import get_logger

logger = get_logger(__name__)

GENESIS_HASH = "0" * 64
HASH_VERSION = "v1"
AUDIT_CHAIN_ADVISORY_LOCK_ID = 492019


def canonical_json_dumps(obj: Any) -> str:
    """Serializes Python object to canonical deterministic JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def compute_payload_hash(
    actor_id: Optional[str],
    actor_role: Optional[str],
    action: str,
    target_type: str,
    target_id: Optional[str],
    metadata: Optional[Dict[str, Any]],
    created_at_iso: str,
) -> str:
    """Computes SHA-256 hash of the canonicalized event payload."""
    payload_dict = {
        "action": str(action).strip(),
        "actor_id": str(actor_id) if actor_id else None,
        "actor_role": str(actor_role) if actor_role else None,
        "created_at": str(created_at_iso).strip(),
        "metadata": metadata or {},
        "target_id": str(target_id) if target_id else None,
        "target_type": str(target_type).strip(),
    }
    canonical_str = canonical_json_dumps(payload_dict)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def compute_event_hash(
    hash_version: str,
    sequence_number: int,
    previous_hash: str,
    payload_hash: str,
) -> str:
    """
    Computes deterministic SHA-256 hash for a chain link:
    SHA-256(version|sequence|previous_hash|payload_hash)
    """
    link_repr = f"{hash_version}|{sequence_number}|{previous_hash.lower()}|{payload_hash.lower()}"
    return hashlib.sha256(link_repr.encode("utf-8")).hexdigest()


async def append_chained_audit_event(
    conn: psycopg.AsyncConnection,
    actor_id: Optional[str],
    actor_role: Optional[str],
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Appends a new audit event atomically to the global tamper-evident hash chain.
    Acquires transactional PostgreSQL advisory lock to ensure serialized, non-conflicting links.
    """
    async with conn.cursor() as cur:
        # 1. Acquire transactional advisory lock to prevent race conditions on sequence/previous_hash
        await cur.execute("SELECT pg_advisory_xact_lock(%s);", (AUDIT_CHAIN_ADVISORY_LOCK_ID,))

        # 2. Find current tip of the audit chain
        await cur.execute(
            """
            SELECT sequence_number, event_hash
            FROM audit_logs
            WHERE sequence_number IS NOT NULL
            ORDER BY sequence_number DESC
            LIMIT 1;
            """
        )
        tip_row = await cur.fetchone()

        if tip_row:
            next_seq = tip_row[0] + 1
            prev_hash = tip_row[1]
        else:
            next_seq = 1
            prev_hash = GENESIS_HASH

        # 3. Deterministic UTC timestamp
        now_dt = datetime.now(timezone.utc)
        created_at_iso = now_dt.isoformat()

        # 4. Hashes
        payload_hash = compute_payload_hash(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
            created_at_iso=created_at_iso,
        )

        event_hash = compute_event_hash(
            hash_version=HASH_VERSION,
            sequence_number=next_seq,
            previous_hash=prev_hash,
            payload_hash=payload_hash,
        )

        # 5. Insert chained audit record
        sql = """
        INSERT INTO audit_logs (
            actor_id, actor_role, action, target_type, target_id, metadata,
            sequence_number, payload_hash, previous_hash, event_hash,
            hash_version, anchoring_status, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'PENDING', %s)
        RETURNING id, actor_id, actor_role, action, target_type, target_id, metadata,
                  sequence_number, payload_hash, previous_hash, event_hash,
                  hash_version, anchoring_status, batch_id, created_at;
        """
        await cur.execute(
            sql,
            (
                actor_id,
                actor_role,
                action,
                target_type,
                target_id,
                json.dumps(metadata or {}),
                next_seq,
                payload_hash,
                prev_hash,
                event_hash,
                HASH_VERSION,
                now_dt,
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to append chained audit event.")

        return {
            "id": str(row[0]),
            "actor_id": str(row[1]) if row[1] else None,
            "actor_role": row[2],
            "action": row[3],
            "target_type": row[4],
            "target_id": str(row[5]) if row[5] else None,
            "metadata": row[6] if isinstance(row[6], dict) else json.loads(row[6] or "{}"),
            "sequence_number": row[7],
            "payload_hash": row[8],
            "previous_hash": row[9],
            "event_hash": row[10],
            "hash_version": row[11],
            "anchoring_status": row[12],
            "batch_id": str(row[13]) if row[13] else None,
            "created_at": row[14].isoformat() if row[14] else None,
        }


async def backfill_legacy_audit_records(
    conn: psycopg.AsyncConnection,
) -> int:
    """
    Idempotent, non-destructive backfill for legacy unchained audit records.
    Establishes a verifiable baseline from existing rows without overwriting or deleting historical data.
    """
    async with conn.cursor() as cur:
        await cur.execute("SELECT pg_advisory_xact_lock(%s);", (AUDIT_CHAIN_ADVISORY_LOCK_ID,))

        # Find current tip
        await cur.execute(
            """
            SELECT sequence_number, event_hash
            FROM audit_logs
            WHERE sequence_number IS NOT NULL
            ORDER BY sequence_number DESC
            LIMIT 1;
            """
        )
        tip_row = await cur.fetchone()
        current_seq = tip_row[0] if tip_row else 0
        current_prev_hash = tip_row[1] if tip_row else GENESIS_HASH

        # Fetch unchained records in chronological order
        await cur.execute(
            """
            SELECT id, actor_id, actor_role, action, target_type, target_id, metadata, created_at
            FROM audit_logs
            WHERE sequence_number IS NULL
            ORDER BY created_at ASC, id ASC;
            """
        )
        unchained_rows = await cur.fetchall()
        if not unchained_rows:
            return 0

        backfilled_count = 0
        for row in unchained_rows:
            event_id = row[0]
            actor_id = str(row[1]) if row[1] else None
            actor_role = row[2]
            action = row[3]
            target_type = row[4]
            target_id = str(row[5]) if row[5] else None
            metadata = row[6] if isinstance(row[6], dict) else json.loads(row[6] or "{}")
            created_at = row[7]
            created_at_iso = created_at.isoformat() if created_at else datetime.now(timezone.utc).isoformat()

            current_seq += 1
            payload_hash = compute_payload_hash(
                actor_id=actor_id,
                actor_role=actor_role,
                action=action,
                target_type=target_type,
                target_id=target_id,
                metadata=metadata,
                created_at_iso=created_at_iso,
            )

            event_hash = compute_event_hash(
                hash_version=HASH_VERSION,
                sequence_number=current_seq,
                previous_hash=current_prev_hash,
                payload_hash=payload_hash,
            )

            await cur.execute(
                """
                UPDATE audit_logs
                SET sequence_number = %s,
                    payload_hash = %s,
                    previous_hash = %s,
                    event_hash = %s,
                    hash_version = %s,
                    anchoring_status = 'PENDING'
                WHERE id = %s AND sequence_number IS NULL;
                """,
                (
                    current_seq,
                    payload_hash,
                    current_prev_hash,
                    event_hash,
                    HASH_VERSION,
                    event_id,
                ),
            )

            current_prev_hash = event_hash
            backfilled_count += 1

        logger.info("Successfully backfilled %d legacy audit log records into audit chain.", backfilled_count)
        return backfilled_count


async def verify_event_chain_integrity(
    conn: psycopg.AsyncConnection,
    event_id: str,
) -> Dict[str, Any]:
    """
    Verifies the cryptographic integrity of an individual audit event:
    1. Recomputes payload hash from stored fields.
    2. Recomputes event hash from (version, sequence, previous_hash, payload_hash).
    3. Checks linkage with the preceding sequence event.
    """
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT id, actor_id, actor_role, action, target_type, target_id, metadata,
                   sequence_number, payload_hash, previous_hash, event_hash,
                   hash_version, anchoring_status, batch_id, created_at
            FROM audit_logs
            WHERE id = %s;
            """,
            (event_id,),
        )
        row = await cur.fetchone()
        if not row:
            return {"outcome": "NOT_FOUND", "message": f"Audit event '{event_id}' not found."}

        event = {
            "id": str(row[0]),
            "actor_id": str(row[1]) if row[1] else None,
            "actor_role": row[2],
            "action": row[3],
            "target_type": row[4],
            "target_id": str(row[5]) if row[5] else None,
            "metadata": row[6] if isinstance(row[6], dict) else json.loads(row[6] or "{}"),
            "sequence_number": row[7],
            "payload_hash": row[8],
            "previous_hash": row[9],
            "event_hash": row[10],
            "hash_version": row[11],
            "anchoring_status": row[12],
            "batch_id": str(row[13]) if row[13] else None,
            "created_at": row[14].isoformat() if row[14] else None,
        }

        if event["sequence_number"] is None:
            return {
                "outcome": "NEEDS_REVIEW",
                "message": "Audit event has not been chained into the hash sequence yet.",
                "event": event,
            }

        # 1. Verify payload hash
        expected_payload_hash = compute_payload_hash(
            actor_id=event["actor_id"],
            actor_role=event["actor_role"],
            action=event["action"],
            target_type=event["target_type"],
            target_id=event["target_id"],
            metadata=event["metadata"],
            created_at_iso=event["created_at"],
        )
        if expected_payload_hash.lower() != (event["payload_hash"] or "").lower():
            return {
                "outcome": "HASH_MISMATCH",
                "message": "Payload hash mismatch: event fields have been modified.",
                "expected": expected_payload_hash,
                "recorded": event["payload_hash"],
                "event": event,
            }

        # 2. Verify event hash
        expected_event_hash = compute_event_hash(
            hash_version=event["hash_version"],
            sequence_number=event["sequence_number"],
            previous_hash=event["previous_hash"],
            payload_hash=event["payload_hash"],
        )
        if expected_event_hash.lower() != (event["event_hash"] or "").lower():
            return {
                "outcome": "HASH_MISMATCH",
                "message": "Event link hash mismatch.",
                "expected": expected_event_hash,
                "recorded": event["event_hash"],
                "event": event,
            }

        # 3. Verify linkage to previous event
        if event["sequence_number"] == 1:
            if event["previous_hash"] != GENESIS_HASH:
                return {
                    "outcome": "PREVIOUS_HASH_MISMATCH",
                    "message": "Genesis link broken: sequence 1 must point to GENESIS_HASH.",
                    "event": event,
                }
        else:
            await cur.execute(
                """
                SELECT event_hash
                FROM audit_logs
                WHERE sequence_number = %s;
                """,
                (event["sequence_number"] - 1,),
            )
            prev_row = await cur.fetchone()
            if not prev_row or prev_row[0].lower() != event["previous_hash"].lower():
                return {
                    "outcome": "PREVIOUS_HASH_MISMATCH",
                    "message": "Previous hash link mismatch: chain continuity broken.",
                    "expected_prev": prev_row[0] if prev_row else None,
                    "recorded_prev": event["previous_hash"],
                    "event": event,
                }

        return {
            "outcome": "VALID",
            "message": "Audit event passes all cryptographic hash-chain integrity checks.",
            "event": event,
        }

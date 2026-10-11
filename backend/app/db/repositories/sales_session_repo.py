"""
Sales session and transcription repository using Psycopg 3 parameterized SQL.
Handles sales conversation sessions, consent records, row-level locks for transcription jobs,
and scoped queries for customer, agent, and authority access.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
import psycopg

from app.core.exceptions import DatabaseException


def _row_to_session_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "customer_id": str(row[1]),
        "agent_id": str(row[2]),
        "policy_id": str(row[3]) if row[3] else None,
        "policy_version_id": str(row[4]) if row[4] else None,
        "registration_id": str(row[5]) if row[5] else None,
        "audio_storage_ref": row[6],
        "audio_mime_type": row[7],
        "audio_file_size_bytes": row[8],
        "duration_seconds": row[9],
        "audio_checksum": row[10],
        "customer_consent": row[11],
        "consent_timestamp": row[12].isoformat() if row[12] else None,
        "consent_notes": row[13],
        "status": row[14],
        "transcript": row[15],
        "detected_language": row[16],
        "word_segments": row[17] if isinstance(row[17], list) else json.loads(row[17] or "[]"),
        "speaker_diarization": row[18] if isinstance(row[18], list) else json.loads(row[18] or "[]"),
        "provider_model": row[19],
        "error_category": row[20],
        "error_message": row[21],
        "created_at": row[22].isoformat() if row[22] else None,
        "updated_at": row[23].isoformat() if row[23] else None,
    }


SESSION_FIELDS = """
    id, customer_id, agent_id, policy_id, policy_version_id, registration_id,
    audio_storage_ref, audio_mime_type, audio_file_size_bytes, duration_seconds,
    audio_checksum, customer_consent, consent_timestamp, consent_notes,
    status, transcript, detected_language, word_segments, speaker_diarization,
    provider_model, error_category, error_message, created_at, updated_at
"""


async def create_sales_session(
    conn: psycopg.AsyncConnection,
    customer_id: str,
    agent_id: str,
    audio_storage_ref: str,
    audio_mime_type: str,
    audio_file_size_bytes: int,
    audio_checksum: str,
    customer_consent: bool,
    policy_id: Optional[str] = None,
    policy_version_id: Optional[str] = None,
    registration_id: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    consent_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Creates a new sales session with customer consent record."""
    sql = f"""
    INSERT INTO sales_sessions (
        customer_id, agent_id, policy_id, policy_version_id, registration_id,
        audio_storage_ref, audio_mime_type, audio_file_size_bytes, duration_seconds,
        audio_checksum, customer_consent, consent_timestamp, consent_notes, status
    )
    VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END, %s, 'PENDING'
    )
    RETURNING {SESSION_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                customer_id,
                agent_id,
                policy_id,
                policy_version_id,
                registration_id,
                audio_storage_ref,
                audio_mime_type,
                audio_file_size_bytes,
                duration_seconds,
                audio_checksum,
                customer_consent,
                customer_consent,
                consent_notes,
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to insert sales session record.")
        return _row_to_session_dict(row)


async def get_session_by_id(
    conn: psycopg.AsyncConnection, session_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieves sales session by UUID."""
    sql = f"SELECT {SESSION_FIELDS} FROM sales_sessions WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (session_id,))
        row = await cur.fetchone()
        return _row_to_session_dict(row) if row else None


async def list_sessions(
    conn: psycopg.AsyncConnection,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Lists sales sessions scoped to role permissions."""
    query = f"SELECT {SESSION_FIELDS} FROM sales_sessions WHERE 1=1"
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
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s;"
    params.extend([limit, offset])

    async with conn.cursor() as cur:
        await cur.execute(query, tuple(params))
        rows = await cur.fetchall()
        return [_row_to_session_dict(r) for r in rows]


async def count_sessions(
    conn: psycopg.AsyncConnection,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    """Counts sessions matching scope filters."""
    query = "SELECT COUNT(*) FROM sales_sessions WHERE 1=1"
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

    async with conn.cursor() as cur:
        await cur.execute(query, tuple(params))
        row = await cur.fetchone()
        return row[0] if row else 0


async def acquire_session_for_transcription_atomic(
    conn: psycopg.AsyncConnection, session_id: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    Acquires row-level lock (FOR UPDATE).
    If status is PENDING or FAILED, transitions status to PROCESSING and returns (True, session).
    If status is already PROCESSING or COMPLETED, returns (False, session) to prevent duplicate jobs.
    """
    lock_sql = f"SELECT {SESSION_FIELDS} FROM sales_sessions WHERE id = %s FOR UPDATE;"
    async with conn.cursor() as cur:
        await cur.execute(lock_sql, (session_id,))
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Sales session not found for transcription lock.")
        session = _row_to_session_dict(row)

        current_status = session["status"]
        if current_status in ("PROCESSING", "COMPLETED"):
            return False, session

        # Transition to PROCESSING
        update_sql = f"""
        UPDATE sales_sessions
        SET status = 'PROCESSING', updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        RETURNING {SESSION_FIELDS};
        """
        await cur.execute(update_sql, (session_id,))
        updated_row = await cur.fetchone()
        if not updated_row:
            raise DatabaseException("Failed to update session to PROCESSING status.")
        return True, _row_to_session_dict(updated_row)


async def update_transcription_success(
    conn: psycopg.AsyncConnection,
    session_id: str,
    transcript: str,
    detected_language: Optional[str],
    word_segments: List[Dict[str, Any]],
    speaker_diarization: List[Dict[str, Any]],
    provider_model: str,
) -> Dict[str, Any]:
    """Records successful ElevenLabs transcription result."""
    sql = f"""
    UPDATE sales_sessions
    SET status = 'COMPLETED',
        transcript = %s,
        detected_language = %s,
        word_segments = %s,
        speaker_diarization = %s,
        provider_model = %s,
        error_category = NULL,
        error_message = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {SESSION_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                transcript,
                detected_language,
                json.dumps(word_segments),
                json.dumps(speaker_diarization),
                provider_model,
                session_id,
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to update transcription success result.")
        return _row_to_session_dict(row)


async def update_transcription_failure(
    conn: psycopg.AsyncConnection,
    session_id: str,
    error_category: str,
    error_message: str,
) -> Dict[str, Any]:
    """Records transcription failure with categorized error."""
    sql = f"""
    UPDATE sales_sessions
    SET status = 'FAILED',
        error_category = %s,
        error_message = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {SESSION_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (error_category, error_message[:1000], session_id))
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to update transcription failure state.")
        return _row_to_session_dict(row)

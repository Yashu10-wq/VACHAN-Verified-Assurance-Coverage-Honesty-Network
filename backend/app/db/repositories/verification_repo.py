"""
Verification reports repository using Psycopg 3 parameterized SQL.
Provides storage, retrieval, and version management for Gemini policy-promise verification reports.
Never overwrites prior reports on reanalysis; increments report_version.
"""

import json
from typing import Any, Dict, List, Optional
import psycopg

from app.core.exceptions import DatabaseException


REPORT_FIELDS = """
    id, sales_session_id, customer_id, agent_id, policy_id, policy_version_id,
    transcript_checksum, report_version, status, model_identifier, summary,
    overall_integrity_status, findings, supported_count, partly_true_count,
    contradicted_count, not_in_policy_count, unclear_count, review_flags,
    error_message, created_at, updated_at
"""


def _row_to_report_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "sales_session_id": str(row[1]),
        "customer_id": str(row[2]),
        "agent_id": str(row[3]),
        "policy_id": str(row[4]),
        "policy_version_id": str(row[5]),
        "transcript_checksum": row[6],
        "report_version": row[7],
        "status": row[8],
        "model_identifier": row[9],
        "summary": row[10],
        "overall_integrity_status": row[11],
        "findings": row[12] if isinstance(row[12], list) else json.loads(row[12] or "[]"),
        "supported_count": row[13],
        "partly_true_count": row[14],
        "contradicted_count": row[15],
        "not_in_policy_count": row[16],
        "unclear_count": row[17],
        "review_flags": row[18] if isinstance(row[18], list) else json.loads(row[18] or "[]"),
        "error_message": row[19],
        "created_at": row[20].isoformat() if row[20] else None,
        "updated_at": row[21].isoformat() if row[21] else None,
    }


async def get_next_report_version(
    conn: psycopg.AsyncConnection,
    sales_session_id: str,
) -> int:
    """Returns the next sequential report_version for the given sales session."""
    sql = "SELECT COALESCE(MAX(report_version), 0) + 1 FROM verification_reports WHERE sales_session_id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (sales_session_id,))
        row = await cur.fetchone()
        return row[0] if row else 1


async def create_verification_report(
    conn: psycopg.AsyncConnection,
    sales_session_id: str,
    customer_id: str,
    agent_id: str,
    policy_id: str,
    policy_version_id: str,
    transcript_checksum: str,
    model_identifier: str = "gemini-2.5-flash",
    status: str = "PENDING",
) -> Dict[str, Any]:
    """Creates a new verification report entry with sequential versioning."""
    next_version = await get_next_report_version(conn, sales_session_id)

    sql = f"""
    INSERT INTO verification_reports (
        sales_session_id, customer_id, agent_id, policy_id, policy_version_id,
        transcript_checksum, report_version, status, model_identifier
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING {REPORT_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                sales_session_id,
                customer_id,
                agent_id,
                policy_id,
                policy_version_id,
                transcript_checksum,
                next_version,
                status,
                model_identifier,
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to create verification report.")
        return _row_to_report_dict(row)


async def update_report_results(
    conn: psycopg.AsyncConnection,
    report_id: str,
    status: str,
    summary: Optional[str] = None,
    overall_integrity_status: Optional[str] = None,
    findings: Optional[List[Dict[str, Any]]] = None,
    supported_count: int = 0,
    partly_true_count: int = 0,
    contradicted_count: int = 0,
    not_in_policy_count: int = 0,
    unclear_count: int = 0,
    review_flags: Optional[List[str]] = None,
    error_message: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Updates verification findings and overall metrics for a report."""
    sql = f"""
    UPDATE verification_reports
    SET status = %s,
        summary = %s,
        overall_integrity_status = %s,
        findings = %s,
        supported_count = %s,
        partly_true_count = %s,
        contradicted_count = %s,
        not_in_policy_count = %s,
        unclear_count = %s,
        review_flags = %s,
        error_message = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {REPORT_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                status,
                summary,
                overall_integrity_status,
                json.dumps(findings or []),
                supported_count,
                partly_true_count,
                contradicted_count,
                not_in_policy_count,
                unclear_count,
                json.dumps(review_flags or []),
                error_message,
                report_id,
            ),
        )
        row = await cur.fetchone()
        return _row_to_report_dict(row) if row else None


async def get_report_by_id(
    conn: psycopg.AsyncConnection,
    report_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieves verification report by UUID."""
    sql = f"SELECT {REPORT_FIELDS} FROM verification_reports WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (report_id,))
        row = await cur.fetchone()
        return _row_to_report_dict(row) if row else None


async def get_latest_report_for_session(
    conn: psycopg.AsyncConnection,
    sales_session_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieves the newest verification report for a sales session."""
    sql = f"""
    SELECT {REPORT_FIELDS}
    FROM verification_reports
    WHERE sales_session_id = %s
    ORDER BY report_version DESC
    LIMIT 1;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (sales_session_id,))
        row = await cur.fetchone()
        return _row_to_report_dict(row) if row else None


async def list_reports_for_session(
    conn: psycopg.AsyncConnection,
    sales_session_id: str,
) -> List[Dict[str, Any]]:
    """Lists all versions of verification reports for a sales session."""
    sql = f"""
    SELECT {REPORT_FIELDS}
    FROM verification_reports
    WHERE sales_session_id = %s
    ORDER BY report_version DESC;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (sales_session_id,))
        rows = await cur.fetchall()
        return [_row_to_report_dict(r) for r in rows]

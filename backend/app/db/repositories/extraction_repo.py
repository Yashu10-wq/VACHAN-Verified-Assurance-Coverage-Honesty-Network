"""
Policy document extraction repository using Psycopg 3 parameterized SQL.
Manages extracted PDF texts, page maps, and checksum caches for policy versions.
"""

import json
from typing import Any, Dict, List, Optional
import psycopg

from app.core.exceptions import DatabaseException


EXTRACTION_FIELDS = """
    id, policy_version_id, document_checksum, status, extracted_text,
    page_count, pages_json, parser_version, error_message, created_at, updated_at
"""


def _row_to_extraction_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "policy_version_id": str(row[1]),
        "document_checksum": row[2],
        "status": row[3],
        "extracted_text": row[4],
        "page_count": row[5],
        "pages_json": row[6] if isinstance(row[6], list) else json.loads(row[6] or "[]"),
        "parser_version": row[7],
        "error_message": row[8],
        "created_at": row[9].isoformat() if row[9] else None,
        "updated_at": row[10].isoformat() if row[10] else None,
    }


async def create_extraction(
    conn: psycopg.AsyncConnection,
    policy_version_id: str,
    document_checksum: str,
    status: str = "PENDING",
    extracted_text: Optional[str] = None,
    page_count: int = 0,
    pages_json: Optional[List[Dict[str, Any]]] = None,
    parser_version: str = "pypdf_v1",
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Creates a new extraction record or returns existing on conflict."""
    sql = f"""
    INSERT INTO policy_document_extractions (
        policy_version_id, document_checksum, status, extracted_text,
        page_count, pages_json, parser_version, error_message
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (policy_version_id, document_checksum)
    DO UPDATE SET
        status = EXCLUDED.status,
        extracted_text = COALESCE(EXCLUDED.extracted_text, policy_document_extractions.extracted_text),
        page_count = EXCLUDED.page_count,
        pages_json = EXCLUDED.pages_json,
        parser_version = EXCLUDED.parser_version,
        error_message = EXCLUDED.error_message,
        updated_at = CURRENT_TIMESTAMP
    RETURNING {EXTRACTION_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                policy_version_id,
                document_checksum,
                status,
                extracted_text,
                page_count,
                json.dumps(pages_json or []),
                parser_version,
                error_message,
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to persist policy document extraction.")
        return _row_to_extraction_dict(row)


async def get_extraction_by_version(
    conn: psycopg.AsyncConnection,
    policy_version_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieves extraction record by policy version ID."""
    sql = f"""
    SELECT {EXTRACTION_FIELDS}
    FROM policy_document_extractions
    WHERE policy_version_id = %s
    ORDER BY created_at DESC
    LIMIT 1;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (policy_version_id,))
        row = await cur.fetchone()
        return _row_to_extraction_dict(row) if row else None


async def get_extraction_by_id(
    conn: psycopg.AsyncConnection,
    extraction_id: str,
) -> Optional[Dict[str, Any]]:
    """Retrieves extraction record by UUID."""
    sql = f"SELECT {EXTRACTION_FIELDS} FROM policy_document_extractions WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (extraction_id,))
        row = await cur.fetchone()
        return _row_to_extraction_dict(row) if row else None


async def update_extraction(
    conn: psycopg.AsyncConnection,
    extraction_id: str,
    status: str,
    extracted_text: Optional[str] = None,
    page_count: int = 0,
    pages_json: Optional[List[Dict[str, Any]]] = None,
    error_message: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Updates extraction results and status."""
    sql = f"""
    UPDATE policy_document_extractions
    SET status = %s,
        extracted_text = %s,
        page_count = %s,
        pages_json = %s,
        error_message = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING {EXTRACTION_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                status,
                extracted_text,
                page_count,
                json.dumps(pages_json or []),
                error_message,
                extraction_id,
            ),
        )
        row = await cur.fetchone()
        return _row_to_extraction_dict(row) if row else None

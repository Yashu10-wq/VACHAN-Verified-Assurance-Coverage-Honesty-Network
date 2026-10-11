"""
Audit logging repository using Psycopg 3 parameterized SQL.
"""

import json
from typing import Any, Dict, Optional
import psycopg


async def log_audit_event(
    conn: psycopg.AsyncConnection,
    actor_id: Optional[str],
    actor_role: Optional[str],
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Inserts a structured security audit event."""
    sql = """
    INSERT INTO audit_logs (actor_id, actor_role, action, target_type, target_id, metadata)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    json_meta = json.dumps(metadata or {})
    async with conn.cursor() as cur:
        await cur.execute(
            sql, (actor_id, actor_role, action, target_type, target_id, json_meta)
        )

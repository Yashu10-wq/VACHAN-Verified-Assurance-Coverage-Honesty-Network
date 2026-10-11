"""
Claim eligibility assessment repository using Psycopg 3 parameterized SQL.
Maintains versioned immutable assessment results with exact numeric balances.
"""

from decimal import Decimal
import json
from typing import Any, Dict, List, Optional
import psycopg

from app.core.exceptions import DatabaseException


def _row_to_assessment_dict(row: tuple) -> Dict[str, Any]:
    return {
        "id": str(row[0]),
        "claim_id": str(row[1]),
        "policy_version_id": str(row[2]),
        "assessment_version": row[3],
        "overall_outcome": row[4],
        "rules_evaluated": row[5] if isinstance(row[5], list) else json.loads(row[5] or "[]"),
        "requested_amount": str(row[6]),
        "applicable_limit": str(row[7]),
        "potentially_payable_amount": str(row[8]),
        "excess_amount": str(row[9]),
        "missing_evidence": row[10] if isinstance(row[10], list) else json.loads(row[10] or "[]"),
        "review_flags": row[11] if isinstance(row[11], list) else json.loads(row[11] or "[]"),
        "assessed_by": str(row[12]) if row[12] else None,
        "created_at": row[13].isoformat() if row[13] else None,
    }


ASSESSMENT_FIELDS = """
    id, claim_id, policy_version_id, assessment_version, overall_outcome,
    rules_evaluated, requested_amount, applicable_limit,
    potentially_payable_amount, excess_amount, missing_evidence,
    review_flags, assessed_by, created_at
"""


async def get_next_assessment_version(
    conn: psycopg.AsyncConnection, claim_id: str
) -> int:
    """Determines the next version number for a claim assessment."""
    sql = "SELECT COALESCE(MAX(assessment_version), 0) + 1 FROM claim_assessments WHERE claim_id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (claim_id,))
        row = await cur.fetchone()
        return row[0] if row else 1


async def create_assessment(
    conn: psycopg.AsyncConnection,
    claim_id: str,
    policy_version_id: str,
    overall_outcome: str,
    rules_evaluated: List[Dict[str, Any]],
    requested_amount: Decimal,
    applicable_limit: Decimal,
    potentially_payable_amount: Decimal,
    excess_amount: Decimal,
    missing_evidence: List[str],
    review_flags: List[str],
    assessed_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Persists a new traceable assessment run for a claim."""
    version = await get_next_assessment_version(conn, claim_id)
    sql = f"""
    INSERT INTO claim_assessments (
        claim_id, policy_version_id, assessment_version, overall_outcome,
        rules_evaluated, requested_amount, applicable_limit,
        potentially_payable_amount, excess_amount, missing_evidence,
        review_flags, assessed_by
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING {ASSESSMENT_FIELDS};
    """
    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (
                claim_id,
                policy_version_id,
                version,
                overall_outcome,
                json.dumps(rules_evaluated),
                requested_amount,
                applicable_limit,
                potentially_payable_amount,
                excess_amount,
                json.dumps(missing_evidence),
                json.dumps(review_flags),
                assessed_by,
            ),
        )
        row = await cur.fetchone()
        if not row:
            raise DatabaseException("Failed to insert claim assessment record.")
        return _row_to_assessment_dict(row)


async def get_latest_assessment(
    conn: psycopg.AsyncConnection, claim_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieves the most recent assessment for a claim."""
    sql = f"""
    SELECT {ASSESSMENT_FIELDS}
    FROM claim_assessments
    WHERE claim_id = %s
    ORDER BY assessment_version DESC
    LIMIT 1;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (claim_id,))
        row = await cur.fetchone()
        return _row_to_assessment_dict(row) if row else None


async def list_assessments_by_claim(
    conn: psycopg.AsyncConnection, claim_id: str
) -> List[Dict[str, Any]]:
    """Lists all historical assessments for a claim in chronological order."""
    sql = f"""
    SELECT {ASSESSMENT_FIELDS}
    FROM claim_assessments
    WHERE claim_id = %s
    ORDER BY assessment_version ASC;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (claim_id,))
        rows = await cur.fetchall()
        return [_row_to_assessment_dict(r) for r in rows]

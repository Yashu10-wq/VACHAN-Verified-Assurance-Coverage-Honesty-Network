"""
Policy-Promise Verification API endpoints for InsureChain VoiceGuard.
Enforces RBAC scoping, grounding validation, and immutable report versioning.
"""

from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, Query, status
import psycopg

from app.api.deps import get_current_active_user
from app.core.exceptions import (
    AuthorizationException,
    NotFoundException,
    ValidationException,
)
from app.core.security import UserRole
from app.db.connection import get_db_connection
from app.db.repositories import (
    audit_repo,
    sales_session_repo,
    verification_repo,
)
from app.schemas.verification import (
    ReanalyzeRequest,
    StartVerificationResponse,
    VerificationReportResponse,
)
from app.services.gemini_verifier import gemini_verifier_service

router = APIRouter(tags=["Policy Verification"])


async def _verify_session_or_report_access(
    conn: psycopg.AsyncConnection,
    user: Dict[str, Any],
    customer_id: str,
    agent_id: str,
) -> None:
    """Enforces RBAC access scoping: Customer (own), Agent (own), Authority (all)."""
    user_role = user.get("role")
    user_id = user.get("id")

    if user_role == UserRole.APPROVAL_AUTHORITY.value:
        return

    if user_role == UserRole.CUSTOMER.value:
        if customer_id != user_id:
            raise NotFoundException("Resource not found.")
        return

    if user_role == UserRole.INSURANCE_AGENT.value:
        if agent_id != user_id:
            raise NotFoundException("Resource not found.")
        return

    raise AuthorizationException("Access denied.")


@router.post(
    "/sales-sessions/{session_id}/verify-policy",
    response_model=VerificationReportResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_sales_session_policy(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Triggers Gemini promise verification of a completed sales session against official policy terms.
    Enforces customer and agent access scoping.
    """
    async with get_db_connection() as conn:
        session = await sales_session_repo.get_session_by_id(conn, session_id)
        if not session:
            raise NotFoundException("Sales session not found.")

        await _verify_session_or_report_access(
            conn=conn,
            user=current_user,
            customer_id=session["customer_id"],
            agent_id=session["agent_id"],
        )

        report = await gemini_verifier_service.verify_sales_session(
            conn=conn,
            sales_session_id=session_id,
            actor_id=current_user["id"],
            actor_role=current_user["role"],
        )
        return report


@router.get(
    "/sales-sessions/{session_id}/verification",
    response_model=Union[VerificationReportResponse, List[VerificationReportResponse]],
)
async def get_session_verification(
    session_id: str,
    all_versions: bool = Query(default=False, description="Return all historical versions if true"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Retrieves the latest verification report or all versioned reports for a sales session."""
    async with get_db_connection() as conn:
        session = await sales_session_repo.get_session_by_id(conn, session_id)
        if not session:
            raise NotFoundException("Sales session not found.")

        await _verify_session_or_report_access(
            conn=conn,
            user=current_user,
            customer_id=session["customer_id"],
            agent_id=session["agent_id"],
        )

        if all_versions:
            reports = await verification_repo.list_reports_for_session(conn, session_id)
            return reports

        latest = await verification_repo.get_latest_report_for_session(conn, session_id)
        if not latest:
            raise NotFoundException("No verification report found for this sales session.")
        return latest


@router.get(
    "/verification-reports/{report_id}",
    response_model=VerificationReportResponse,
)
async def get_verification_report(
    report_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Retrieves a specific verification report by UUID."""
    async with get_db_connection() as conn:
        report = await verification_repo.get_report_by_id(conn, report_id)
        if not report:
            raise NotFoundException("Verification report not found.")

        await _verify_session_or_report_access(
            conn=conn,
            user=current_user,
            customer_id=report["customer_id"],
            agent_id=report["agent_id"],
        )

        return report


@router.post(
    "/verification-reports/{report_id}/reanalyze",
    response_model=VerificationReportResponse,
    status_code=status.HTTP_200_OK,
)
async def reanalyze_verification_report(
    report_id: str,
    body: Optional[ReanalyzeRequest] = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Triggers re-analysis of the underlying sales session without overwriting prior reports.
    Increments report_version sequentially.
    """
    async with get_db_connection() as conn:
        old_report = await verification_repo.get_report_by_id(conn, report_id)
        if not old_report:
            raise NotFoundException("Verification report not found.")

        await _verify_session_or_report_access(
            conn=conn,
            user=current_user,
            customer_id=old_report["customer_id"],
            agent_id=old_report["agent_id"],
        )

        session_id = old_report["sales_session_id"]

        # Run fresh verification producing an incremental version
        new_report = await gemini_verifier_service.verify_sales_session(
            conn=conn,
            sales_session_id=session_id,
            actor_id=current_user["id"],
            actor_role=current_user["role"],
        )

        # Audit reanalysis request
        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_user["id"],
            actor_role=current_user["role"],
            action="REANALYZE_VERIFICATION",
            target_type="verification_report",
            target_id=new_report["id"],
            metadata={
                "previous_report_id": report_id,
                "previous_version": old_report["report_version"],
                "new_version": new_report["report_version"],
                "reason": body.reason if body else None,
            },
        )

        return new_report

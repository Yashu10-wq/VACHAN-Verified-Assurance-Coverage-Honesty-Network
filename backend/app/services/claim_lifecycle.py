"""
Claim Lifecycle State Machine and Transition Service for InsureChain VoiceGuard.
Enforces strict lifecycle state transitions, role authorizations, mandatory audit reasons,
and concurrency control.
"""

from typing import Any, Dict, Optional, Set, Tuple
import psycopg

from app.core.exceptions import (
    AuthorizationException,
    ConflictException,
    ValidationException,
)
from app.core.security import ClaimStatus, UserRole
from app.db.repositories.audit_repo import log_audit_event
from app.db.repositories.claim_repo import update_claim_status_atomic


# Allowed transitions map: current_status -> set of allowed target_statuses
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    ClaimStatus.SUBMITTED.value: {ClaimStatus.UNDER_REVIEW.value},
    ClaimStatus.UNDER_REVIEW.value: {
        ClaimStatus.EVIDENCE_REQUESTED.value,
        ClaimStatus.APPROVED.value,
        ClaimStatus.REJECTED.value,
    },
    ClaimStatus.EVIDENCE_REQUESTED.value: {ClaimStatus.UNDER_REVIEW.value},
    ClaimStatus.APPROVED.value: {ClaimStatus.PAID.value},
    ClaimStatus.REJECTED.value: set(),
    ClaimStatus.PAID.value: set(),
}

# Role permissions for each transition: (from_status, to_status) -> set of allowed UserRoles
TRANSITION_PERMISSIONS: Dict[Tuple[str, str], Set[str]] = {
    (ClaimStatus.SUBMITTED.value, ClaimStatus.UNDER_REVIEW.value): {UserRole.APPROVAL_AUTHORITY.value},
    (ClaimStatus.UNDER_REVIEW.value, ClaimStatus.EVIDENCE_REQUESTED.value): {UserRole.APPROVAL_AUTHORITY.value},
    (ClaimStatus.EVIDENCE_REQUESTED.value, ClaimStatus.UNDER_REVIEW.value): {
        UserRole.CUSTOMER.value,
        UserRole.APPROVAL_AUTHORITY.value,
    },
    (ClaimStatus.UNDER_REVIEW.value, ClaimStatus.APPROVED.value): {UserRole.APPROVAL_AUTHORITY.value},
    (ClaimStatus.UNDER_REVIEW.value, ClaimStatus.REJECTED.value): {UserRole.APPROVAL_AUTHORITY.value},
    (ClaimStatus.APPROVED.value, ClaimStatus.PAID.value): {UserRole.APPROVAL_AUTHORITY.value},
}


class ClaimLifecycleService:
    """
    Manages state machine transitions with database transactions and audit events.
    """

    async def transition_status(
        self,
        conn: psycopg.AsyncConnection,
        claim: Dict[str, Any],
        target_status: ClaimStatus,
        actor_id: str,
        actor_role: str,
        reason: str,
        decision_metadata: Optional[Dict[str, Any]] = None,
        is_simulated_payment: bool = False,
    ) -> Dict[str, Any]:
        current_status = claim["status"]
        to_status = target_status.value
        claim_id = claim["id"]

        # Reason validation
        if not reason or len(reason.strip()) < 5:
            raise ValidationException("A clear decision reason (minimum 5 characters) is required for state transitions.")

        # Insurance agents are strictly prohibited from performing any claim transitions
        if actor_role == UserRole.INSURANCE_AGENT.value:
            raise AuthorizationException("Insurance agents are not authorized to transition claim statuses.")

        # Check allowed target status according to state machine
        allowed_targets = ALLOWED_TRANSITIONS.get(current_status, set())
        if to_status not in allowed_targets:
            raise ConflictException(
                f"Invalid claim transition: Cannot transition from '{current_status}' to '{to_status}'. "
                f"Allowed transitions from '{current_status}' are: {list(allowed_targets) or 'None (terminal state)'}."
            )

        # Check actor role permission for this specific transition
        transition_key = (current_status, to_status)
        allowed_roles = TRANSITION_PERMISSIONS.get(transition_key, set())
        if actor_role not in allowed_roles:
            raise AuthorizationException(
                f"Role '{actor_role}' is not authorized to transition claim from '{current_status}' to '{to_status}'. "
                f"Required role(s): {list(allowed_roles)}."
            )

        # If actor is CUSTOMER, ensure they own the claim
        if actor_role == UserRole.CUSTOMER.value and claim["customer_id"] != actor_id:
            raise AuthorizationException("Customer cannot transition claims belonging to another user.")

        # If transitioning from APPROVED to PAID, require simulated payment flag
        if transition_key == (ClaimStatus.APPROVED.value, ClaimStatus.PAID.value) and not is_simulated_payment:
            raise ValidationException("Transition to PAID requires explicit simulated payment authorization.")

        audit_correlation_id = f"trans_{claim_id[:8]}_{to_status.lower()}"

        try:
            prev_status, updated_claim = await update_claim_status_atomic(
                conn=conn,
                claim_id=claim_id,
                new_status=to_status,
                actor_id=actor_id,
                actor_role=actor_role,
                reason=reason,
                decision_metadata=decision_metadata,
                audit_correlation_id=audit_correlation_id,
            )

            # Audit action name mapping
            action_map = {
                ClaimStatus.UNDER_REVIEW.value: "CLAIM_REVIEW_STARTED" if prev_status == ClaimStatus.SUBMITTED.value else "CLAIM_REVIEW_RESUMED",
                ClaimStatus.EVIDENCE_REQUESTED.value: "CLAIM_EVIDENCE_REQUESTED",
                ClaimStatus.APPROVED.value: "CLAIM_APPROVED",
                ClaimStatus.REJECTED.value: "CLAIM_REJECTED",
                ClaimStatus.PAID.value: "CLAIM_PAYMENT_SIMULATED",
            }
            audit_action = action_map.get(to_status, "CLAIM_STATUS_TRANSITIONED")

            await log_audit_event(
                conn=conn,
                actor_id=actor_id,
                actor_role=actor_role,
                action=audit_action,
                target_type="claim",
                target_id=claim_id,
                metadata={
                    "previous_status": prev_status,
                    "new_status": to_status,
                    "reason": reason,
                    "decision_metadata": decision_metadata or {},
                },
            )

            return updated_claim

        except Exception as exc:
            # Log transition failure if safe
            await log_audit_event(
                conn=conn,
                actor_id=actor_id,
                actor_role=actor_role,
                action="CLAIM_TRANSITION_FAILED",
                target_type="claim",
                target_id=claim_id,
                metadata={
                    "attempted_target_status": to_status,
                    "error_type": type(exc).__name__,
                },
            )
            raise


claim_lifecycle_service = ClaimLifecycleService()

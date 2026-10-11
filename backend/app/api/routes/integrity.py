"""
Blockchain Audit Anchoring and Integrity Verification API routes for InsureChain VoiceGuard.
Enforces scoped RBAC, Merkle proof derivations, on-chain commitment checks, and authority admin controls.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
import psycopg

from app.api.deps import get_current_active_user, require_active_authority
from app.core.exceptions import (
    AuthorizationException,
    NotFoundException,
    ValidationException,
)
from app.core.security import UserRole
from app.db.connection import get_db_connection
from app.db.repositories import anchor_batch_repo, audit_repo
from app.schemas.integrity import (
    AnchorPendingResponse,
    AuditEventProofResponse,
    AuditEventVerificationResponse,
    BackfillResponse,
    BlockchainStatusResponse,
    MerkleProofStep,
    VerifyRequest,
)
from app.services.audit_chain import backfill_legacy_audit_records, verify_event_chain_integrity
from app.services.blockchain_service import blockchain_service
from app.services.merkle_tree import MerkleTree, verify_merkle_proof

router = APIRouter(prefix="/integrity", tags=["Blockchain Audit Anchoring"])


def _verify_audit_event_access(user: Dict[str, Any], event: Dict[str, Any]) -> None:
    """Enforces scoped RBAC on audit records. Fails closed with 404 to prevent info leakage."""
    role = user.get("role")
    user_id = user.get("id")

    if role == UserRole.APPROVAL_AUTHORITY.value:
        return

    # Check actor match
    if event.get("actor_id") == user_id:
        return

    # Check metadata match for customer / agent
    meta = event.get("metadata") or {}
    if role == UserRole.CUSTOMER.value:
        if meta.get("customer_id") == user_id:
            return
        raise NotFoundException("Audit event not found.")

    if role == UserRole.INSURANCE_AGENT.value:
        if meta.get("agent_id") == user_id:
            return
        raise NotFoundException("Audit event not found.")

    raise AuthorizationException("Access denied to audit event.")


@router.get("/status", response_model=BlockchainStatusResponse)
async def get_integrity_and_blockchain_status(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Returns blockchain connectivity, smart contract status, and audit anchoring statistics.
    Never exposes private keys, RPC secrets, or sensitive credentials.
    """
    async with get_db_connection() as conn:
        counts = await anchor_batch_repo.get_anchoring_counts(conn)
        bc_status = await blockchain_service.get_blockchain_status()

        return {
            "is_connected": bc_status["is_connected"],
            "rpc_url": bc_status["rpc_url"],
            "configured_chain_id": bc_status["configured_chain_id"],
            "node_chain_id": bc_status["node_chain_id"],
            "block_number": bc_status["block_number"],
            "contract_address": bc_status["contract_address"],
            "contract_deployed": bc_status["contract_deployed"],
            "status": bc_status["status"],
            "total_events": counts["total_events"],
            "unchained_events": counts["unchained_events"],
            "pending_events": counts["pending_events"],
            "batched_events": counts["batched_events"],
            "anchored_events": counts["anchored_events"],
            "failed_events": counts["failed_events"],
        }


@router.get("/audit-events/{event_id}", response_model=AuditEventVerificationResponse)
async def verify_audit_event(
    event_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Verifies local hash, previous-hash linkage, and chain integrity for an individual audit event.
    Cross-checks with smart contract if anchored on-chain.
    """
    async with get_db_connection() as conn:
        result = await verify_event_chain_integrity(conn, event_id)
        if result["outcome"] == "NOT_FOUND":
            raise NotFoundException(f"Audit event '{event_id}' not found.")

        event = result.get("event")
        if event:
            _verify_audit_event_access(current_user, event)

        on_chain_verified = False
        outcome = result["outcome"]
        message = result["message"]

        # If locally valid and batched/anchored, check on-chain commitment
        if outcome == "VALID" and event and event.get("batch_id"):
            batch = await anchor_batch_repo.get_batch_by_id(conn, event["batch_id"])
            if batch and batch.get("status") == "ANCHORED":
                chain_res = await blockchain_service.verify_commitment_on_chain(batch["batch_root_hash"])
                if chain_res.get("exists"):
                    on_chain_verified = True
                else:
                    outcome = "ANCHOR_NOT_FOUND"
                    message = "Batch root recorded as anchored in DB was not found on-chain."
            elif batch and batch.get("status") in ("PENDING", "SUBMITTING"):
                outcome = "ANCHOR_PENDING"
                message = "Audit event is batched and awaiting on-chain block confirmation."

        return {
            "event_id": event_id,
            "outcome": outcome,
            "message": message,
            "sequence_number": event.get("sequence_number") if event else None,
            "event_hash": event.get("event_hash") if event else None,
            "previous_hash": event.get("previous_hash") if event else None,
            "payload_hash": event.get("payload_hash") if event else None,
            "anchoring_status": event.get("anchoring_status") if event else None,
            "batch_id": event.get("batch_id") if event else None,
            "created_at": event.get("created_at") if event else None,
            "on_chain_verified": on_chain_verified,
        }


@router.get("/audit-events/{event_id}/proof", response_model=AuditEventProofResponse)
async def get_audit_event_proof(
    event_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Derives cryptographic Merkle inclusion proof and on-chain commitment details for an audit event.
    """
    async with get_db_connection() as conn:
        event = await audit_repo.get_audit_event_by_id(conn, event_id)
        if not event:
            raise NotFoundException("Audit event not found.")

        _verify_audit_event_access(current_user, event)

        batch_id = event.get("batch_id")
        if not batch_id:
            raise ValidationException("Audit event has not been included in an anchored batch yet.")

        batch = await anchor_batch_repo.get_batch_by_id(conn, batch_id)
        if not batch:
            raise NotFoundException("Associated anchor batch record not found.")

        # Fetch all events in this batch ordered by sequence
        batch_events = await anchor_batch_repo.get_events_for_batch(conn, batch_id)
        leaf_hashes = [e["event_hash"] for e in batch_events]

        try:
            leaf_index = next(i for i, e in enumerate(batch_events) if e["id"] == event_id)
        except StopIteration:
            raise ValidationException("Event hash not found among batch leaves.")

        # Derive Merkle proof
        tree = MerkleTree(leaf_hashes)
        proof = tree.get_proof(leaf_index)

        # Standalone verification check
        is_locally_valid = verify_merkle_proof(
            leaf_hash=event["event_hash"],
            proof=proof,
            expected_root=batch["batch_root_hash"].replace("0x", ""),
        )
        if not is_locally_valid:
            raise ValidationException("Computed Merkle proof does not evaluate to recorded batch root.")

        # Check on-chain commitment
        chain_res = await blockchain_service.verify_commitment_on_chain(batch["batch_root_hash"])
        on_chain_verified = bool(chain_res.get("exists"))

        proof_steps = [
            MerkleProofStep(position=step["position"], hash=step["hash"])
            for step in proof
        ]

        return {
            "event_id": event_id,
            "sequence_number": event["sequence_number"],
            "event_hash": event["event_hash"],
            "batch_id": batch_id,
            "batch_sequence": batch["batch_sequence"],
            "batch_root_hash": batch["batch_root_hash"],
            "leaf_index": leaf_index,
            "merkle_proof": proof_steps,
            "tx_hash": batch.get("tx_hash"),
            "block_number": batch.get("block_number"),
            "chain_id": batch.get("chain_id"),
            "contract_address": batch.get("contract_address"),
            "on_chain_commitment_verified": on_chain_verified,
            "anchored_at": batch.get("anchored_at"),
        }


@router.post("/verify", response_model=List[AuditEventVerificationResponse])
async def verify_multiple_audit_events(
    body: VerifyRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """
    Verifies cryptographic hash-chain integrity for a list of up to 50 audit event UUIDs.
    """
    results: List[Dict[str, Any]] = []

    async with get_db_connection() as conn:
        for event_id in body.event_ids:
            res = await verify_event_chain_integrity(conn, event_id)
            if res["outcome"] == "NOT_FOUND":
                results.append({
                    "event_id": event_id,
                    "outcome": "NOT_FOUND",
                    "message": f"Audit event '{event_id}' not found.",
                })
                continue

            event = res.get("event")
            # Permission check: if unauthorized, omit from response or fail closed with NOT_FOUND
            try:
                if event:
                    _verify_audit_event_access(current_user, event)
            except Exception:
                results.append({
                    "event_id": event_id,
                    "outcome": "NOT_FOUND",
                    "message": "Resource not found or unauthorized.",
                })
                continue

            on_chain_verified = False
            outcome = res["outcome"]
            message = res["message"]

            if outcome == "VALID" and event and event.get("batch_id"):
                batch = await anchor_batch_repo.get_batch_by_id(conn, event["batch_id"])
                if batch and batch.get("status") == "ANCHORED":
                    chain_res = await blockchain_service.verify_commitment_on_chain(batch["batch_root_hash"])
                    if chain_res.get("exists"):
                        on_chain_verified = True
                    else:
                        outcome = "ANCHOR_NOT_FOUND"
                        message = "Batch root recorded as anchored was not found on-chain."

            results.append({
                "event_id": event_id,
                "outcome": outcome,
                "message": message,
                "sequence_number": event.get("sequence_number") if event else None,
                "event_hash": event.get("event_hash") if event else None,
                "previous_hash": event.get("previous_hash") if event else None,
                "payload_hash": event.get("payload_hash") if event else None,
                "anchoring_status": event.get("anchoring_status") if event else None,
                "batch_id": event.get("batch_id") if event else None,
                "created_at": event.get("created_at") if event else None,
                "on_chain_verified": on_chain_verified,
            })

    return results


@router.post(
    "/anchor-pending",
    response_model=AnchorPendingResponse,
    status_code=status.HTTP_200_OK,
)
async def trigger_anchor_pending_batches(
    current_authority: Dict[str, Any] = Depends(require_active_authority),
) -> Dict[str, Any]:
    """
    Administrative endpoint to trigger Merkle batch creation and on-chain anchoring for pending events.
    Restricted to Approval Authorities only.
    """
    async with get_db_connection() as conn:
        res = await blockchain_service.process_pending_audit_batches(
            conn=conn,
            actor_id=current_authority["id"],
            actor_role=current_authority["role"],
        )
        return {
            "batches_created": res.get("batches_created", 0),
            "anchored_events": res.get("anchored_events", 0),
            "status": res.get("status", "COMPLETED"),
            "message": res.get("message", res.get("error", "Processed pending batches.")),
        }


@router.post(
    "/backfill",
    response_model=BackfillResponse,
    status_code=status.HTTP_200_OK,
)
async def trigger_legacy_audit_backfill(
    current_authority: Dict[str, Any] = Depends(require_active_authority),
) -> Dict[str, Any]:
    """
    Administrative endpoint to non-destructively chain unsequenced historical audit logs.
    Restricted to Approval Authorities only.
    """
    async with get_db_connection() as conn:
        count = await backfill_legacy_audit_records(conn)
        return {
            "backfilled_count": count,
            "message": f"Successfully backfilled {count} legacy audit event(s) into the audit hash chain.",
        }

"""
Policy catalogue and version management endpoints.
Enforces authority permissions for creation and publishing.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_active_user, require_active_authority
from app.core.exceptions import ConflictException, ResourceNotFoundException
from app.db.connection import get_db_connection
from app.db.repositories import audit_repo, policy_repo
from app.schemas.policy import (
    CreatePolicyRequest,
    CreatePolicyVersionRequest,
    PolicyResponse,
    PolicyVersionResponse,
)

router = APIRouter(prefix="/policies", tags=["Policy Catalogue"])


@router.get("", response_model=List[PolicyResponse])
async def list_active_policies(
    category: Optional[str] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """Lists published active insurance policies with their current published version."""
    async with get_db_connection() as conn:
        policies = await policy_repo.list_policies(conn, category=category, is_active=True)
        results = []
        for p in policies:
            latest = await policy_repo.get_published_version(conn, p["id"])
            p_dict = dict(p)
            p_dict["latest_version"] = latest
            results.append(p_dict)
        return results


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy_detail(
    policy_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Retrieves policy details and published terms."""
    async with get_db_connection() as conn:
        policy = await policy_repo.get_policy_by_id(conn, policy_id)
        if not policy:
            raise ResourceNotFoundException("Policy not found.")

        latest_version = await policy_repo.get_published_version(conn, policy_id)
        policy_dict = dict(policy)
        policy_dict["latest_version"] = latest_version
        return policy_dict


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_policy(
    body: CreatePolicyRequest,
    current_authority: Dict[str, Any] = Depends(require_active_authority),
) -> Dict[str, Any]:
    """Authority-only endpoint to define a new policy scheme."""
    async with get_db_connection() as conn:
        existing = await policy_repo.get_policy_by_code(conn, body.policy_code)
        if existing:
            raise ConflictException(f"Policy with code '{body.policy_code}' already exists.")

        policy = await policy_repo.create_policy(
            conn=conn,
            insurer_name=body.insurer_name,
            policy_name=body.policy_name,
            policy_code=body.policy_code,
            category=body.category.value,
            description=body.description,
            coverage_limit=body.coverage_limit,
            waiting_period_days=body.waiting_period_days,
            claim_filing_window_days=body.claim_filing_window_days,
            created_by=current_authority["id"],
        )

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_authority["id"],
            actor_role=current_authority["role"],
            action="CREATE_POLICY",
            target_type="policy",
            target_id=policy["id"],
            metadata={"code": body.policy_code, "category": body.category.value},
        )

        return policy


@router.post("/{policy_id}/versions", response_model=PolicyVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_policy_version(
    policy_id: str,
    body: CreatePolicyVersionRequest,
    current_authority: Dict[str, Any] = Depends(require_active_authority),
) -> Dict[str, Any]:
    """Authority-only endpoint to upload versioned terms and document checksum."""
    async with get_db_connection() as conn:
        policy = await policy_repo.get_policy_by_id(conn, policy_id)
        if not policy:
            raise ResourceNotFoundException("Policy not found.")

        version = await policy_repo.create_policy_version(
            conn=conn,
            policy_id=policy_id,
            version_number=body.version_number,
            document_storage_ref=body.document_storage_ref,
            document_checksum=body.document_checksum,
            effective_date=body.effective_date,
            expiry_date=body.expiry_date,
            terms_json=body.terms_json,
        )

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_authority["id"],
            actor_role=current_authority["role"],
            action="CREATE_POLICY_VERSION",
            target_type="policy_version",
            target_id=version["id"],
            metadata={"policy_id": policy_id, "version": body.version_number},
        )

        return version


@router.post("/{policy_id}/versions/{version_id}/publish", response_model=PolicyVersionResponse)
async def publish_policy_version(
    policy_id: str,
    version_id: str,
    current_authority: Dict[str, Any] = Depends(require_active_authority),
) -> Dict[str, Any]:
    """Authority-only endpoint to publish a policy version, making it eligible for registrations."""
    async with get_db_connection() as conn:
        version = await policy_repo.get_policy_version_by_id(conn, version_id)
        if not version or version["policy_id"] != policy_id:
            raise ResourceNotFoundException("Policy version not found.")

        published = await policy_repo.publish_policy_version(
            conn=conn, version_id=version_id, published_by=current_authority["id"]
        )
        if not published:
            raise ResourceNotFoundException("Failed to publish version.")

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_authority["id"],
            actor_role=current_authority["role"],
            action="PUBLISH_POLICY_VERSION",
            target_type="policy_version",
            target_id=version_id,
            metadata={"policy_id": policy_id, "version": version["version_number"]},
        )

        return published

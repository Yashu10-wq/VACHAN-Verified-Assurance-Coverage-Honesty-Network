"""
Automated test suite for Phase 3: Policy Catalogue and Versioning.
Tests authority-restricted creation, version publication, and catalogue retrieval.
"""

from decimal import Decimal
import uuid
import httpx
import pytest

from app.core.config import get_settings


async def get_bootstrap_authority_token(client: httpx.AsyncClient) -> str:
    """Helper to bootstrap and log in as an active authority."""
    settings = get_settings()
    email = f"auth_policy_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "AuthorityPassword123!"
    await client.post(
        "/api/v1/auth/bootstrap-authority",
        json={
            "email": email,
            "password": pwd,
            "full_name": "Policy Authority",
            "bootstrap_secret": settings.AUTHORITY_BOOTSTRAP_SECRET,
        },
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    return login.json()["access_token"]


async def get_verified_customer_token(client: httpx.AsyncClient) -> str:
    """Helper to register, verify, and log in as an active customer."""
    from app.services.email_service import EmailService

    email = f"cust_policy_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "CustomerPassword123!"
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": pwd, "full_name": "Policy Customer", "role": "CUSTOMER"},
    )
    raw_token = [m for m in EmailService.sent_messages if m.to_email == email][-1].token
    await client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    return login.json()["access_token"]


@pytest.mark.asyncio
async def test_policy_creation_authority_only(async_client: httpx.AsyncClient):
    """Verifies that only active authorities may create policies."""
    auth_token = await get_bootstrap_authority_token(async_client)
    cust_token = await get_verified_customer_token(async_client)

    code = f"POL-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "insurer_name": "Vortexa Mutual Assurance",
        "policy_name": "Complete Health Shield",
        "policy_code": code,
        "category": "HOSPITALIZATION",
        "description": "Comprehensive cashless medical and hospitalization protection.",
        "coverage_limit": "500000.00",
        "waiting_period_days": 30,
        "claim_filing_window_days": 15,
    }

    # 1. Customer attempt is rejected (403 Forbidden)
    cust_attempt = await async_client.post(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {cust_token}"},
        json=payload,
    )
    assert cust_attempt.status_code == 403

    # 2. Authority attempt succeeds (201 Created)
    auth_attempt = await async_client.post(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=payload,
    )
    assert auth_attempt.status_code == 201
    created_policy = auth_attempt.json()
    assert created_policy["policy_code"] == code
    assert created_policy["coverage_limit"] == 500000.00

    # 3. Duplicate policy code rejected (409 Conflict)
    dup_attempt = await async_client.post(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=payload,
    )
    assert dup_attempt.status_code == 409


@pytest.mark.asyncio
async def test_policy_version_and_publishing_workflow(async_client: httpx.AsyncClient):
    """Tests creating a policy version, publishing it, and verifying catalogue presence."""
    auth_token = await get_bootstrap_authority_token(async_client)
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    code = f"VEH-{uuid.uuid4().hex[:6].upper()}"
    # Create master policy
    pol_res = await async_client.post(
        "/api/v1/policies",
        headers=auth_headers,
        json={
            "insurer_name": "National Motor Shield",
            "policy_name": "Comprehensive Motor AutoCare",
            "policy_code": code,
            "category": "VEHICLE",
            "description": "Accidental damage and third party coverage.",
            "coverage_limit": "250000.00",
            "waiting_period_days": 0,
            "claim_filing_window_days": 7,
        },
    )
    policy_id = pol_res.json()["id"]

    # Upload version 1
    doc_checksum = "a" * 64
    ver_res = await async_client.post(
        f"/api/v1/policies/{policy_id}/versions",
        headers=auth_headers,
        json={
            "version_number": 1,
            "document_storage_ref": "cloudinary://vachan/policies/vehicle_v1.pdf",
            "document_checksum": doc_checksum,
            "effective_date": "2026-01-01",
            "terms_json": {"roadside_assistance": True, "deductible": 1000},
        },
    )
    assert ver_res.status_code == 201
    version_id = ver_res.json()["id"]
    assert ver_res.json()["is_published"] is False

    # Publish version 1
    pub_res = await async_client.post(
        f"/api/v1/policies/{policy_id}/versions/{version_id}/publish",
        headers=auth_headers,
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["is_published"] is True

    # Check catalogue list
    list_res = await async_client.get(
        f"/api/v1/policies/{policy_id}",
        headers=auth_headers,
    )
    assert list_res.status_code == 200
    pol_detail = list_res.json()
    assert pol_detail["latest_version"] is not None
    assert pol_detail["latest_version"]["version_number"] == 1
    assert pol_detail["latest_version"]["document_checksum"] == doc_checksum

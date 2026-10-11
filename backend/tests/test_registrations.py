"""
Automated test suite for Phase 3: Agent Customer Registration and Customer Confirmation.
Tests consent validation, scoped visibility, invitation emails, and affirmative customer confirmation.
"""

import uuid
import httpx
import pytest

from app.core.config import get_settings
from app.services.email_service import EmailService


async def setup_test_actors(client: httpx.AsyncClient):
    """Sets up an active authority, active agent, and active customer."""
    settings = get_settings()

    # 1. Authority
    auth_email = f"auth_reg_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "AuthorityPassword123!"
    await client.post(
        "/api/v1/auth/bootstrap-authority",
        json={
            "email": auth_email,
            "password": pwd,
            "full_name": "Registration Authority",
            "bootstrap_secret": settings.AUTHORITY_BOOTSTRAP_SECRET,
        },
    )
    auth_login = await client.post("/api/v1/auth/login", json={"email": auth_email, "password": pwd})
    auth_token = auth_login.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # 2. Agent (signed up and approved by authority)
    agent_email = f"agent_reg_{uuid.uuid4().hex[:6]}@example.com"
    agent_signup = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": agent_email,
            "password": pwd,
            "full_name": "Field Agent",
            "role": "INSURANCE_AGENT",
        },
    )
    agent_id = agent_signup.json()["id"]
    await client.post(
        "/api/v1/auth/approve-account",
        headers=auth_headers,
        json={"user_id": agent_id, "status": "ACTIVE"},
    )
    agent_login = await client.post("/api/v1/auth/login", json={"email": agent_email, "password": pwd})
    agent_token = agent_login.json()["access_token"]

    # 3. Customer (signed up and verified)
    cust_email = f"cust_reg_{uuid.uuid4().hex[:6]}@example.com"
    cust_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": cust_email, "password": pwd, "full_name": "Confirmed Customer", "role": "CUSTOMER"},
    )
    cust_id = cust_signup.json()["id"]
    raw_token = [m for m in EmailService.sent_messages if m.to_email == cust_email][-1].token
    await client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    cust_login = await client.post("/api/v1/auth/login", json={"email": cust_email, "password": pwd})
    cust_token = cust_login.json()["access_token"]

    # 4. Create and publish a test policy
    pol_res = await client.post(
        "/api/v1/policies",
        headers=auth_headers,
        json={
            "insurer_name": "Vortexa Life & Health",
            "policy_name": "Arogya Sanjeevani Standard",
            "policy_code": f"AROGYA-{uuid.uuid4().hex[:6].upper()}",
            "category": "HOSPITALIZATION",
            "description": "Standard hospitalization benefits.",
            "coverage_limit": "300000.00",
            "waiting_period_days": 30,
            "claim_filing_window_days": 30,
        },
    )
    policy_id = pol_res.json()["id"]
    ver_res = await client.post(
        f"/api/v1/policies/{policy_id}/versions",
        headers=auth_headers,
        json={
            "version_number": 1,
            "document_storage_ref": "cloudinary://vachan/policies/arogya_v1.pdf",
            "document_checksum": "b" * 64,
            "effective_date": "2026-01-01",
        },
    )
    version_id = ver_res.json()["id"]
    await client.post(
        f"/api/v1/policies/{policy_id}/versions/{version_id}/publish",
        headers=auth_headers,
    )

    return {
        "auth_token": auth_token,
        "agent_token": agent_token,
        "agent_id": agent_id,
        "cust_token": cust_token,
        "cust_id": cust_id,
        "cust_email": cust_email,
        "policy_id": policy_id,
        "version_id": version_id,
    }


@pytest.mark.asyncio
async def test_agent_registration_and_customer_confirmation_flow(async_client: httpx.AsyncClient):
    """
    Tests the complete end-to-end flow:
    1. Agent registers customer with consent.
    2. Customer views pending registration.
    3. Customer explicitly confirms.
    4. Registration status becomes CONFIRMED.
    """
    actors = await setup_test_actors(async_client)
    agent_headers = {"Authorization": f"Bearer {actors['agent_token']}"}
    cust_headers = {"Authorization": f"Bearer {actors['cust_token']}"}

    # 1. Agent registers customer
    reg_payload = {
        "customer_id": actors["cust_id"],
        "policy_id": actors["policy_id"],
        "policy_version_id": actors["version_id"],
        "customer_consent": True,
        "consent_notes": "Verbal affirmative consent recorded during sales consultation.",
    }
    create_res = await async_client.post(
        "/api/v1/registrations",
        headers=agent_headers,
        json=reg_payload,
    )
    assert create_res.status_code == 201
    reg_data = create_res.json()
    registration_id = reg_data["id"]
    assert reg_data["customer_id"] == actors["cust_id"]
    assert reg_data["status"] == "PENDING_VERIFICATION"

    # 2. Agent cannot confirm on behalf of customer (Must be 403 Forbidden)
    agent_confirm_attempt = await async_client.post(
        f"/api/v1/registrations/{registration_id}/confirm",
        headers=agent_headers,
    )
    assert agent_confirm_attempt.status_code == 403

    # 3. Customer lists their own registrations
    cust_list = await async_client.get("/api/v1/registrations", headers=cust_headers)
    assert cust_list.status_code == 200
    matching_regs = [r for r in cust_list.json() if r["id"] == registration_id]
    assert len(matching_regs) == 1

    # 4. Designated customer explicitly confirms the policy
    confirm_res = await async_client.post(
        f"/api/v1/registrations/{registration_id}/confirm",
        headers=cust_headers,
    )
    assert confirm_res.status_code == 200
    confirmed_data = confirm_res.json()
    assert confirmed_data["status"] == "CONFIRMED"
    assert confirmed_data["activated_at"] is not None
    assert confirmed_data["customer_decision_at"] is not None


@pytest.mark.asyncio
async def test_customer_decline_flow(async_client: httpx.AsyncClient):
    """Verifies that a customer can decline a pending registration."""
    actors = await setup_test_actors(async_client)
    agent_headers = {"Authorization": f"Bearer {actors['agent_token']}"}
    cust_headers = {"Authorization": f"Bearer {actors['cust_token']}"}

    # Agent creates registration
    create_res = await async_client.post(
        "/api/v1/registrations",
        headers=agent_headers,
        json={
            "customer_id": actors["cust_id"],
            "policy_id": actors["policy_id"],
            "policy_version_id": actors["version_id"],
            "customer_consent": True,
        },
    )
    registration_id = create_res.json()["id"]

    # Customer declines
    decline_res = await async_client.post(
        f"/api/v1/registrations/{registration_id}/decline",
        headers=cust_headers,
    )
    assert decline_res.status_code == 200
    assert decline_res.json()["status"] == "DECLINED"
    assert decline_res.json()["declined_at"] is not None


@pytest.mark.asyncio
async def test_unauthorized_customer_cannot_confirm_other_registration(async_client: httpx.AsyncClient):
    """Verifies that customer A cannot confirm a policy registered for customer B."""
    actors = await setup_test_actors(async_client)
    agent_headers = {"Authorization": f"Bearer {actors['agent_token']}"}

    # Create another customer (Customer B)
    other_email = f"other_cust_{uuid.uuid4().hex[:6]}@example.com"
    await async_client.post(
        "/api/v1/auth/signup",
        json={"email": other_email, "password": "Password123!", "full_name": "Customer B", "role": "CUSTOMER"},
    )
    raw_token = [m for m in EmailService.sent_messages if m.to_email == other_email][-1].token
    await async_client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    login_b = await async_client.post("/api/v1/auth/login", json={"email": other_email, "password": "Password123!"})
    token_b = login_b.json()["access_token"]

    # Agent creates registration for Customer A
    reg_res = await async_client.post(
        "/api/v1/registrations",
        headers=agent_headers,
        json={
            "customer_id": actors["cust_id"],
            "policy_id": actors["policy_id"],
            "policy_version_id": actors["version_id"],
            "customer_consent": True,
        },
    )
    reg_id = reg_res.json()["id"]

    # Customer B attempts to confirm Customer A's registration (Must be 403 Forbidden)
    b_attempt = await async_client.post(
        f"/api/v1/registrations/{reg_id}/confirm",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_attempt.status_code == 403

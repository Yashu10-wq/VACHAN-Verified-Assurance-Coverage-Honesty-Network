"""
Automated test suite for Phase 2: Authentication, Identity, and RBAC.
Tests password hashing, token validation, signup per role, email verification,
login lifecycle, refresh rotation, password reset, and authority approval.
"""

from datetime import datetime, timedelta, timezone
import uuid
import httpx
import pytest

from app.core.config import get_settings
from app.core.security import (
    AccountStatus,
    UserRole,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.email_service import EmailService


def test_password_hashing():
    """Verifies Argon2id password hashing and comparison."""
    password = "SuperSecurePassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_access_token_lifecycle():
    """Verifies token creation, decoding, and expiration."""
    user_id = str(uuid.uuid4())
    token = create_access_token({"sub": user_id, "role": UserRole.CUSTOMER.value})
    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == UserRole.CUSTOMER.value

    # Expired token
    expired_token = create_access_token(
        {"sub": user_id, "role": UserRole.CUSTOMER.value},
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(Exception):
        decode_access_token(expired_token)


@pytest.mark.asyncio
async def test_public_signup_roles_and_statuses(async_client: httpx.AsyncClient):
    """
    Verifies that public signup enforces role-specific initial account statuses:
    - CUSTOMER: PENDING_VERIFICATION
    - INSURANCE_AGENT: PENDING_APPROVAL
    - APPROVAL_AUTHORITY: PENDING_APPROVAL (cannot self-grant privileges)
    """
    unique_suffix = uuid.uuid4().hex[:6]

    # 1. Customer signup
    cust_res = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"cust_{unique_suffix}@example.com",
            "password": "Password123!",
            "full_name": "Test Customer",
            "role": "CUSTOMER",
        },
    )
    assert cust_res.status_code == 201
    cust_data = cust_res.json()
    assert cust_data["role"] == "CUSTOMER"
    assert cust_data["account_status"] == "PENDING_VERIFICATION"

    # 2. Agent signup
    agent_res = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"agent_{unique_suffix}@example.com",
            "password": "Password123!",
            "full_name": "Test Agent",
            "role": "INSURANCE_AGENT",
        },
    )
    assert agent_res.status_code == 201
    agent_data = agent_res.json()
    assert agent_data["role"] == "INSURANCE_AGENT"
    assert agent_data["account_status"] == "PENDING_APPROVAL"

    # 3. Authority public signup (Must remain unprivileged PENDING_APPROVAL!)
    auth_res = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"auth_{unique_suffix}@example.com",
            "password": "Password123!",
            "full_name": "Public Authority Request",
            "role": "APPROVAL_AUTHORITY",
        },
    )
    assert auth_res.status_code == 201
    auth_data = auth_res.json()
    assert auth_data["role"] == "APPROVAL_AUTHORITY"
    assert auth_data["account_status"] == "PENDING_APPROVAL"


@pytest.mark.asyncio
async def test_duplicate_signup_rejection(async_client: httpx.AsyncClient):
    """Verifies that duplicate email signups are safely rejected with 409 Conflict."""
    email = f"dup_{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "Duplicate User",
        "role": "CUSTOMER",
    }
    first = await async_client.post("/api/v1/auth/signup", json=payload)
    assert first.status_code == 201

    second = await async_client.post("/api/v1/auth/signup", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_email_verification_and_login_flow(async_client: httpx.AsyncClient):
    """
    Tests complete customer verification lifecycle:
    Unverified cannot login -> Verify with token -> Login succeeds.
    """
    email = f"verify_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "Password123!"

    # 1. Signup
    signup_res = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": pwd, "full_name": "Verify Me", "role": "CUSTOMER"},
    )
    assert signup_res.status_code == 201

    # 2. Attempt login before verification (must fail 403)
    login_fail = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    assert login_fail.status_code == 403
    assert "verification required" in login_fail.json()["error"].lower()

    # 3. Extract verification token from recorded sent messages
    matching = [m for m in EmailService.sent_messages if m.to_email == email]
    assert len(matching) >= 1
    raw_token = matching[-1].token

    # 4. Verify email
    verify_res = await async_client.post(
        "/api/v1/auth/verify-email",
        json={"token": raw_token},
    )
    assert verify_res.status_code == 200

    # 5. Token cannot be reused (single-use)
    reuse_res = await async_client.post(
        "/api/v1/auth/verify-email",
        json={"token": raw_token},
    )
    assert reuse_res.status_code == 422

    # 6. Login now succeeds
    login_ok = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    assert login_ok.status_code == 200
    token_data = login_ok.json()
    assert "access_token" in token_data
    assert token_data["user"]["account_status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_logout(async_client: httpx.AsyncClient):
    """Verifies refresh token rotation and revocation upon logout."""
    email = f"refresh_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "Password123!"

    # Signup & verify
    await async_client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": pwd, "full_name": "Token Tester", "role": "CUSTOMER"},
    )
    raw_token = [m for m in EmailService.sent_messages if m.to_email == email][-1].token
    await async_client.post("/api/v1/auth/verify-email", json={"token": raw_token})

    # Login
    login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    data = login_res.json()
    refresh_1 = data["refresh_token"]

    # Rotate refresh token
    rotate_res = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert rotate_res.status_code == 200
    refresh_2 = rotate_res.json()["refresh_token"]
    assert refresh_2 != refresh_1

    # Old refresh token is revoked
    old_use = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_1})
    assert old_use.status_code == 401

    # Logout
    logout_res = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {rotate_res.json()['access_token']}"},
        json={"refresh_token": refresh_2},
    )
    assert logout_res.status_code == 200

    # Revoked token cannot be refreshed
    revoked_use = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_2})
    assert revoked_use.status_code == 401


@pytest.mark.asyncio
async def test_authority_bootstrap_and_account_approval(async_client: httpx.AsyncClient):
    """
    Tests operator-controlled authority bootstrap and subsequent account approval.
    """
    settings = get_settings()
    auth_email = f"super_auth_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "SuperAuthorityPass123!"

    # 1. Invalid secret rejected
    bad_boot = await async_client.post(
        "/api/v1/auth/bootstrap-authority",
        json={
            "email": auth_email,
            "password": pwd,
            "full_name": "Root Authority",
            "bootstrap_secret": "invalid_secret",
        },
    )
    assert bad_boot.status_code == 403

    # 2. Valid bootstrap succeeds
    boot_res = await async_client.post(
        "/api/v1/auth/bootstrap-authority",
        json={
            "email": auth_email,
            "password": pwd,
            "full_name": "Root Authority",
            "bootstrap_secret": settings.AUTHORITY_BOOTSTRAP_SECRET,
        },
    )
    assert boot_res.status_code == 201
    assert boot_res.json()["account_status"] == "ACTIVE"

    # 3. Log in as authority
    login_auth = await async_client.post(
        "/api/v1/auth/login", json={"email": auth_email, "password": pwd}
    )
    auth_token = login_auth.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # 4. Sign up pending agent
    agent_email = f"pending_agent_{uuid.uuid4().hex[:6]}@example.com"
    agent_signup = await async_client.post(
        "/api/v1/auth/signup",
        json={
            "email": agent_email,
            "password": "Password123!",
            "full_name": "Agent Awaiting Approval",
            "role": "INSURANCE_AGENT",
        },
    )
    agent_id = agent_signup.json()["id"]

    # 5. Authority approves agent
    approve_res = await async_client.post(
        "/api/v1/auth/approve-account",
        headers={**auth_headers},
        json={"user_id": agent_id, "status": "ACTIVE"},
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["account_status"] == "ACTIVE"

    # 6. Approved agent can now log in
    agent_login = await async_client.post(
        "/api/v1/auth/login", json={"email": agent_email, "password": "Password123!"}
    )
    assert agent_login.status_code == 200

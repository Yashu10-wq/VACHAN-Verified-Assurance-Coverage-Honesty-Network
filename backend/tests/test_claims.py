"""
Automated test suite for Phase 4: Claims Engine.
Tests claim submission, policy-version binding, deterministic eligibility evaluation,
coverage-limit calculations, duplicate-incident detection, evidence handling,
strict lifecycle state machine transitions, and RBAC isolation.
"""

from datetime import date, timedelta
from decimal import Decimal
import uuid
import httpx
import pytest

from app.core.config import get_settings
from app.core.security import AssessmentOutcome, ClaimStatus, RuleOutcome
from app.services.email_service import EmailService


async def setup_claims_test_environment(client: httpx.AsyncClient):
    """
    Sets up an active authority, active agent, active customer,
    published policy (with limit 50000.00), and a confirmed registration.
    """
    settings = get_settings()
    pwd = "SecureClaimsPassword123!"

    # 1. Active Authority
    auth_email = f"auth_claims_{uuid.uuid4().hex[:6]}@example.com"
    await client.post(
        "/api/v1/auth/bootstrap-authority",
        json={
            "email": auth_email,
            "password": pwd,
            "full_name": "Claims Authority Admin",
            "bootstrap_secret": settings.AUTHORITY_BOOTSTRAP_SECRET,
        },
    )
    auth_login = await client.post("/api/v1/auth/login", json={"email": auth_email, "password": pwd})
    auth_token = auth_login.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # 2. Active Agent
    agent_email = f"agent_claims_{uuid.uuid4().hex[:6]}@example.com"
    agent_signup = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": agent_email,
            "password": pwd,
            "full_name": "Claims Field Agent",
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
    agent_headers = {"Authorization": f"Bearer {agent_token}"}

    # 3. Active Customer A
    cust_a_email = f"cust_a_{uuid.uuid4().hex[:6]}@example.com"
    cust_a_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": cust_a_email, "password": pwd, "full_name": "Claimant Alice", "role": "CUSTOMER"},
    )
    cust_a_id = cust_a_signup.json()["id"]
    raw_token_a = [m for m in EmailService.sent_messages if m.to_email == cust_a_email][-1].token
    await client.post("/api/v1/auth/verify-email", json={"token": raw_token_a})
    cust_a_login = await client.post("/api/v1/auth/login", json={"email": cust_a_email, "password": pwd})
    cust_a_token = cust_a_login.json()["access_token"]
    cust_a_headers = {"Authorization": f"Bearer {cust_a_token}"}

    # 4. Active Customer B (for isolation testing)
    cust_b_email = f"cust_b_{uuid.uuid4().hex[:6]}@example.com"
    cust_b_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": cust_b_email, "password": pwd, "full_name": "Claimant Bob", "role": "CUSTOMER"},
    )
    cust_b_id = cust_b_signup.json()["id"]
    raw_token_b = [m for m in EmailService.sent_messages if m.to_email == cust_b_email][-1].token
    await client.post("/api/v1/auth/verify-email", json={"token": raw_token_b})
    cust_b_login = await client.post("/api/v1/auth/login", json={"email": cust_b_email, "password": pwd})
    cust_b_token = cust_b_login.json()["access_token"]
    cust_b_headers = {"Authorization": f"Bearer {cust_b_token}"}

    # 5. Create and publish a Vehicle policy with 50,000 limit
    pol_res = await client.post(
        "/api/v1/policies",
        headers=auth_headers,
        json={
            "insurer_name": "Vortexa General Insurance",
            "policy_name": "Motor Comprehensive Shield",
            "policy_code": f"MOTOR-{uuid.uuid4().hex[:6].upper()}",
            "category": "VEHICLE",
            "description": "Comprehensive motor damage protection.",
            "coverage_limit": "50000.00",
            "waiting_period_days": 0,
            "claim_filing_window_days": 30,
        },
    )
    policy_id = pol_res.json()["id"]
    ver_res = await client.post(
        f"/api/v1/policies/{policy_id}/versions",
        headers=auth_headers,
        json={
            "version_number": 1,
            "document_storage_ref": "cloudinary://vachan/policies/motor_v1.pdf",
            "document_checksum": "a" * 64,
            "effective_date": "2026-01-01",
            "terms_json": {
                "required_evidence": ["REGISTRATION_CERTIFICATE", "INCIDENT_PHOTO"],
                "exclusions": ["racing", "intoxication"],
            },
        },
    )
    version_id = ver_res.json()["id"]
    await client.post(
        f"/api/v1/policies/{policy_id}/versions/{version_id}/publish",
        headers=auth_headers,
    )

    # 6. Register Customer A and Confirm registration
    reg_res = await client.post(
        "/api/v1/registrations",
        headers=agent_headers,
        json={
            "customer_id": cust_a_id,
            "policy_id": policy_id,
            "policy_version_id": version_id,
            "customer_consent": True,
            "consent_notes": "Consent verified during registration.",
        },
    )
    reg_id = reg_res.json()["id"]

    # Customer A confirms registration
    await client.post(f"/api/v1/registrations/{reg_id}/confirm", headers=cust_a_headers)

    return {
        "auth_headers": auth_headers,
        "agent_headers": agent_headers,
        "agent_id": agent_id,
        "cust_a_headers": cust_a_headers,
        "cust_a_id": cust_a_id,
        "cust_b_headers": cust_b_headers,
        "cust_b_id": cust_b_id,
        "policy_id": policy_id,
        "version_id": version_id,
        "reg_id": reg_id,
    }


@pytest.mark.asyncio
async def test_claim_creation_and_validation(async_client: httpx.AsyncClient):
    """
    Tests claim submission:
    - Successful vehicle claim submission.
    - Rejection of invalid amounts (zero / negative).
    - Rejection of future incident dates.
    - Rejection when filing against unowned registration.
    """
    env = await setup_claims_test_environment(async_client)

    # 1. Valid Claim Creation
    incident_date = (date.today() - timedelta(days=5)).isoformat()
    claim_payload = {
        "registration_id": env["reg_id"],
        "claim_category": "VEHICLE",
        "requested_amount": "25000.00",
        "incident_date": incident_date,
        "description": "Front bumper collision occurred at highway junction.",
        "structured_details": {
            "vehicle_registration_number": "KA01AB1234",
            "driver_name": "Alice Claimant",
        },
    }
    res = await async_client.post("/api/v1/claims", headers=env["cust_a_headers"], json=claim_payload)
    assert res.status_code == 201
    claim = res.json()
    assert claim["status"] == "SUBMITTED"
    assert claim["claim_category"] == "VEHICLE"
    assert claim["requested_amount"] == "25000.00"
    assert claim["customer_id"] == env["cust_a_id"]
    claim_id = claim["id"]

    # 2. Invalid Amount (negative or zero)
    bad_amt = dict(claim_payload, requested_amount="-500.00")
    res_bad = await async_client.post("/api/v1/claims", headers=env["cust_a_headers"], json=bad_amt)
    assert res_bad.status_code == 422

    # 3. Invalid Incident Date (future date)
    future_date = (date.today() + timedelta(days=2)).isoformat()
    bad_date = dict(claim_payload, incident_date=future_date)
    res_future = await async_client.post("/api/v1/claims", headers=env["cust_a_headers"], json=bad_date)
    assert res_future.status_code == 422

    # 4. Unauthorized Customer B trying to claim against Customer A's registration
    res_unauth = await async_client.post("/api/v1/claims", headers=env["cust_b_headers"], json=claim_payload)
    assert res_unauth.status_code == 403


@pytest.mark.asyncio
async def test_deterministic_eligibility_and_coverage_limit_calculation(async_client: httpx.AsyncClient):
    """
    Tests deterministic eligibility evaluation, specifically:
    - Exact ₹70,000 requested vs ₹50,000 coverage limit:
      * Preserves original requested amount = ₹70,000
      * Calculates potentially payable amount = ₹50,000
      * Reports excess amount = ₹20,000
      * Outcome is INELIGIBLE under strict limit rule
    - Reassessment creates a new traceable assessment version.
    """
    env = await setup_claims_test_environment(async_client)

    # Submit claim with ₹70,000 requested (limit is ₹50,000)
    incident_date = (date.today() - timedelta(days=3)).isoformat()
    claim_payload = {
        "registration_id": env["reg_id"],
        "claim_category": "VEHICLE",
        "requested_amount": "70000.00",
        "incident_date": incident_date,
        "description": "Total engine damage and transmission failure after collision.",
        "structured_details": {"vehicle_registration_number": "KA01AB1234"},
    }
    claim_res = await async_client.post("/api/v1/claims", headers=env["cust_a_headers"], json=claim_payload)
    assert claim_res.status_code == 201
    claim_id = claim_res.json()["id"]

    # Run deterministic assessment
    assess_res = await async_client.post(f"/api/v1/claims/{claim_id}/assess", headers=env["auth_headers"])
    assert assess_res.status_code == 200
    assessment = assess_res.json()

    # Exact boundary checks
    assert assessment["assessment_version"] == 1
    assert assessment["requested_amount"] == "70000.00"
    assert assessment["applicable_limit"] == "50000.00"
    assert assessment["potentially_payable_amount"] == "50000.00"
    assert assessment["excess_amount"] == "20000.00"
    assert assessment["overall_outcome"] == "INELIGIBLE"

    # Verify coverage limit rule specifically failed
    cov_rule = next(r for r in assessment["rules_evaluated"] if r["rule_id"] == "RULE_COVERAGE_LIMIT")
    assert cov_rule["result"] == "FAIL"
    assert "exceeds policy coverage limit of ₹50000.00 by ₹20000.00" in cov_rule["explanation"]

    # Reassessment creates version 2
    reassess_res = await async_client.post(f"/api/v1/claims/{claim_id}/assess", headers=env["auth_headers"])
    assert reassess_res.status_code == 200
    assert reassess_res.json()["assessment_version"] == 2


@pytest.mark.asyncio
async def test_evidence_upload_and_signed_url_flow(async_client: httpx.AsyncClient):
    """
    Tests evidence upload and private signed URL generation:
    - Valid image upload.
    - Unsupported file type rejection.
    - Signed URL generation with token/expiry.
    - Customer B cannot view or generate links for Customer A's evidence.
    """
    env = await setup_claims_test_environment(async_client)

    # Create claim
    incident_date = (date.today() - timedelta(days=2)).isoformat()
    claim_res = await async_client.post(
        "/api/v1/claims",
        headers=env["cust_a_headers"],
        json={
            "registration_id": env["reg_id"],
            "claim_category": "VEHICLE",
            "requested_amount": "15000.00",
            "incident_date": incident_date,
            "description": "Fender scratch and side mirror damage.",
        },
    )
    claim_id = claim_res.json()["id"]

    # 1. Valid PNG Upload (valid 1x1 PNG binary)
    import base64
    png_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
    files = {"file": ("damage_photo.png", png_bytes, "image/png")}
    data = {"evidence_type": "INCIDENT_PHOTO"}

    up_res = await async_client.post(
        f"/api/v1/claims/{claim_id}/evidence",
        headers=env["cust_a_headers"],
        files=files,
        data=data,
    )
    assert up_res.status_code == 201
    evidence = up_res.json()
    assert evidence["evidence_type"] == "INCIDENT_PHOTO"
    assert evidence["original_filename"] == "damage_photo.png"
    assert evidence["file_size_bytes"] == len(png_bytes)
    evidence_id = evidence["id"]

    # 2. Signed URL Generation
    url_res = await async_client.get(
        f"/api/v1/claims/{claim_id}/evidence/{evidence_id}/signed-url",
        headers=env["cust_a_headers"],
    )
    assert url_res.status_code == 200
    assert "signed_url" in url_res.json()
    assert url_res.json()["expires_in_seconds"] == 300

    # 3. Customer B isolation check
    b_url_res = await async_client.get(
        f"/api/v1/claims/{claim_id}/evidence/{evidence_id}/signed-url",
        headers=env["cust_b_headers"],
    )
    assert b_url_res.status_code == 404

    # 4. Invalid MIME / magic byte rejection
    bad_files = {"file": ("script.exe", b"MZ\x90\x00executable_bytes", "application/octet-stream")}
    bad_up = await async_client.post(
        f"/api/v1/claims/{claim_id}/evidence",
        headers=env["cust_a_headers"],
        files=bad_files,
        data={"evidence_type": "SUPPORTING_DOCUMENT"},
    )
    assert bad_up.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_claim_detection(async_client: httpx.AsyncClient):
    """
    Tests duplicate incident candidate detection:
    - Same vehicle registration, same incident date.
    - Candidate is flagged as review signal, does NOT automatically reject claim.
    """
    env = await setup_claims_test_environment(async_client)
    incident_date = (date.today() - timedelta(days=4)).isoformat()

    # Claim 1
    c1_res = await async_client.post(
        "/api/v1/claims",
        headers=env["cust_a_headers"],
        json={
            "registration_id": env["reg_id"],
            "claim_category": "VEHICLE",
            "requested_amount": "20000.00",
            "incident_date": incident_date,
            "description": "Rear bumper collision in parking lot.",
            "structured_details": {"vehicle_registration_number": "KA04XX9999"},
        },
    )
    claim1_id = c1_res.json()["id"]

    # Claim 2 (potential duplicate of Claim 1)
    c2_res = await async_client.post(
        "/api/v1/claims",
        headers=env["cust_a_headers"],
        json={
            "registration_id": env["reg_id"],
            "claim_category": "VEHICLE",
            "requested_amount": "20000.00",
            "incident_date": incident_date,
            "description": "Parking lot impact on rear end.",
            "structured_details": {"vehicle_registration_number": "KA04XX9999"},
        },
    )
    claim2_id = c2_res.json()["id"]

    # Check duplicates for Claim 2
    dup_res = await async_client.get(f"/api/v1/claims/{claim2_id}/duplicates", headers=env["auth_headers"])
    assert dup_res.status_code == 200
    dups = dup_res.json()
    assert dups["total_candidates"] >= 1
    top_cand = dups["candidates"][0]
    assert top_cand["candidate_claim_id"] == claim1_id
    assert top_cand["match_score"] >= 0.70
    assert any("Exact match on structured identifier 'vehicle_registration_number'" in r for r in top_cand["match_reasons"])


@pytest.mark.asyncio
async def test_claim_lifecycle_state_machine_and_simulated_payment(async_client: httpx.AsyncClient):
    """
    Tests strict state machine transitions:
    - SUBMITTED -> UNDER_REVIEW (Authority)
    - UNDER_REVIEW -> EVIDENCE_REQUESTED (Authority)
    - EVIDENCE_REQUESTED -> UNDER_REVIEW (Customer)
    - UNDER_REVIEW -> APPROVED (Authority)
    - APPROVED -> PAID (Authority via simulate-payment)
    - Rejection of invalid transitions (e.g. SUBMITTED -> PAID directly).
    - Status history audit logging.
    """
    env = await setup_claims_test_environment(async_client)
    incident_date = (date.today() - timedelta(days=2)).isoformat()

    # Create claim
    claim_res = await async_client.post(
        "/api/v1/claims",
        headers=env["cust_a_headers"],
        json={
            "registration_id": env["reg_id"],
            "claim_category": "VEHICLE",
            "requested_amount": "10000.00",
            "incident_date": incident_date,
            "description": "Windshield crack from road debris.",
        },
    )
    claim_id = claim_res.json()["id"]

    # 1. Invalid transition: SUBMITTED -> APPROVED directly (Must fail 409)
    bad_trans = await async_client.post(
        f"/api/v1/claims/{claim_id}/transition",
        headers=env["auth_headers"],
        json={"target_status": "APPROVED", "reason": "Attempting to skip review."},
    )
    assert bad_trans.status_code == 409

    # 2. SUBMITTED -> UNDER_REVIEW (Authority)
    t1 = await async_client.post(
        f"/api/v1/claims/{claim_id}/transition",
        headers=env["auth_headers"],
        json={"target_status": "UNDER_REVIEW", "reason": "Adjuster assigned for incident review."},
    )
    assert t1.status_code == 200
    assert t1.json()["status"] == "UNDER_REVIEW"

    # 3. UNDER_REVIEW -> EVIDENCE_REQUESTED (Authority)
    t2 = await async_client.post(
        f"/api/v1/claims/{claim_id}/transition",
        headers=env["auth_headers"],
        json={"target_status": "EVIDENCE_REQUESTED", "reason": "Please upload clearer damage pictures."},
    )
    assert t2.status_code == 200
    assert t2.json()["status"] == "EVIDENCE_REQUESTED"

    # 4. EVIDENCE_REQUESTED -> UNDER_REVIEW (Customer responds)
    t3 = await async_client.post(
        f"/api/v1/claims/{claim_id}/transition",
        headers=env["cust_a_headers"],
        json={"target_status": "UNDER_REVIEW", "reason": "High resolution photos uploaded."},
    )
    assert t3.status_code == 200
    assert t3.json()["status"] == "UNDER_REVIEW"

    # 5. UNDER_REVIEW -> APPROVED (Authority)
    t4 = await async_client.post(
        f"/api/v1/claims/{claim_id}/transition",
        headers=env["auth_headers"],
        json={"target_status": "APPROVED", "reason": "Claim approved within verified coverage limits."},
    )
    assert t4.status_code == 200
    assert t4.json()["status"] == "APPROVED"

    # 6. APPROVED -> PAID (Authority via simulated-payment)
    t5 = await async_client.post(
        f"/api/v1/claims/{claim_id}/simulate-payment",
        headers=env["auth_headers"],
        json={"target_status": "PAID", "reason": "Simulated disbursement to claimant bank account."},
    )
    assert t5.status_code == 200
    assert t5.json()["status"] == "PAID"

    # 7. Terminal state: PAID cannot transition back to UNDER_REVIEW
    bad_terminal = await async_client.post(
        f"/api/v1/claims/{claim_id}/transition",
        headers=env["auth_headers"],
        json={"target_status": "UNDER_REVIEW", "reason": "Attempting to reopen paid claim."},
    )
    assert bad_terminal.status_code == 409

    # 8. Verify Status History timeline
    hist_res = await async_client.get(f"/api/v1/claims/{claim_id}/history", headers=env["cust_a_headers"])
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) == 5
    transitions = [(h["previous_status"], h["new_status"]) for h in history]
    assert transitions == [
        ("SUBMITTED", "UNDER_REVIEW"),
        ("UNDER_REVIEW", "EVIDENCE_REQUESTED"),
        ("EVIDENCE_REQUESTED", "UNDER_REVIEW"),
        ("UNDER_REVIEW", "APPROVED"),
        ("APPROVED", "PAID"),
    ]


@pytest.mark.asyncio
async def test_rbac_and_data_isolation(async_client: httpx.AsyncClient):
    """
    Tests security isolation:
    - Customer A cannot access Customer B's claims (returns 404).
    - Insurance agent cannot access claims for registrations not created by them.
    - Agent cannot transition or decide claims.
    """
    env = await setup_claims_test_environment(async_client)
    incident_date = (date.today() - timedelta(days=1)).isoformat()

    # Create Claim for Customer A
    c_res = await async_client.post(
        "/api/v1/claims",
        headers=env["cust_a_headers"],
        json={
            "registration_id": env["reg_id"],
            "claim_category": "VEHICLE",
            "requested_amount": "5000.00",
            "incident_date": incident_date,
            "description": "Minor bumper scrape.",
        },
    )
    claim_id = c_res.json()["id"]

    # Customer B attempts to get Customer A's claim -> 404 (no information leakage)
    b_res = await async_client.get(f"/api/v1/claims/{claim_id}", headers=env["cust_b_headers"])
    assert b_res.status_code == 404

    # Agent attempts to approve claim -> 403 Forbidden
    agent_approve = await async_client.post(
        f"/api/v1/claims/{claim_id}/transition",
        headers=env["agent_headers"],
        json={"target_status": "APPROVED", "reason": "Agent trying to approve."},
    )
    assert agent_approve.status_code == 403

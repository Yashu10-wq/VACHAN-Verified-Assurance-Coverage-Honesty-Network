"""
Comprehensive test suite for Phase 6: Gemini Policy-Promise Verification.
Tests PDF extraction, grounding validation, hallucination detection, 5-tier classification,
metrics calculation, RBAC isolation, and sequential version incrementing on reanalysis.
"""

from unittest.mock import AsyncMock, patch
import uuid
import httpx
from pypdf import PdfWriter
import pytest

from app.core.config import get_settings
from app.db.connection import get_db_connection
from app.db.repositories import (
    policy_repo,
    sales_session_repo,
    verification_repo,
)
from app.schemas.verification import (
    OverallIntegrityStatus,
    PromiseVerdict,
    ValidationStatus,
)
from app.services.email_service import EmailService
from app.services.gemini_verifier import (
    gemini_verifier_service,
    normalize_text_for_matching,
    verify_grounding,
)
from app.services.policy_extractor import (
    detect_section_headings,
    policy_extractor_service,
)


# ==============================================================================
# 1. Unit Tests for Extractor and Grounding Validator
# ==============================================================================

def test_detect_section_headings():
    """Tests regex detection of standard insurance section and clause headings."""
    sample_text = """
    SECTION 1. ELIGIBILITY
    All individuals aged 18-65 are eligible.
    Clause 2.3 Waiting Periods
    Pre-existing conditions require 90 days.
    EXCLUSIONS
    Cosmetic and aesthetic treatments are not covered.
    Random normal sentence here.
    """
    headings = detect_section_headings(sample_text)
    assert any("SECTION 1. ELIGIBILITY" in h for h in headings)
    assert any("Clause 2.3 Waiting Periods" in h for h in headings)
    assert any("EXCLUSIONS" in h for h in headings)


def test_pdf_extraction_scanned_or_blank_detection():
    """Tests that a blank PDF without digital text is marked as NEEDS_REVIEW."""
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    import io
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    text, page_count, pages_json, status = policy_extractor_service.extract_from_pdf_bytes(pdf_bytes)
    assert page_count == 1
    assert status == "NEEDS_REVIEW"


def test_verify_grounding_substring_logic():
    """Tests strict verbatim quote containment check against source document."""
    transcript = "Agent: Yes sir, your dental procedures are 100% covered without deductible."
    quote_valid = "dental procedures are 100% covered"
    quote_hallucinated = "vision and eye surgery is included for free"

    assert verify_grounding(quote_valid, transcript) is True
    assert verify_grounding(quote_hallucinated, transcript) is False


def test_grounding_validation_flags_hallucinated_quotes():
    """
    Tests that findings quoting nonexistent transcript lines or nonexistent policy clauses
    are marked with INVALID_QUOTE / UNVERIFIED_CITATION and trigger review_required.
    """
    transcript = "Agent: We cover hospitalization up to 500000 rupees."
    policy_text = "Section 1: Inpatient hospitalization is covered up to 500000 rupees with 30-day waiting."

    raw_findings = [
        {
            "promise_text": "Hospitalization covered",
            "transcript_quote": "hospitalization up to 500000 rupees",
            "speaker_label": "Agent",
            "classification": "SUPPORTED",
            "policy_excerpt": "Inpatient hospitalization is covered up to 500000 rupees",
            "explanation": "Explicitly confirmed.",
            "confidence": 0.98,
        },
        {
            "promise_text": "Free LASIK surgery included",
            "transcript_quote": "I promise we give you free LASIK eye care",  # NOT in transcript
            "speaker_label": "Agent",
            "classification": "SUPPORTED",
            "policy_excerpt": "LASIK eye surgery is covered in full",  # NOT in policy
            "explanation": "Claimed benefit.",
            "confidence": 0.95,
        },
    ]

    findings, flags = gemini_verifier_service.validate_and_ground_findings(
        raw_findings=raw_findings,
        transcript=transcript,
        policy_text=policy_text,
    )

    # First finding should be GROUNDED
    assert findings[0]["validation_status"] == ValidationStatus.GROUNDED.value
    assert findings[0]["review_required"] is False

    # Second finding has hallucinated transcript quote and policy excerpt
    assert findings[1]["validation_status"] == ValidationStatus.INVALID_QUOTE.value
    assert findings[1]["review_required"] is True
    assert len(flags) > 0


def test_metrics_and_overall_integrity_calculation():
    """Tests status determination rules."""
    # 1. Contradicted present -> MISLEADING_CLAIMS_DETECTED
    f_contradicted = [
        {"classification": "SUPPORTED"},
        {"classification": "CONTRADICTED"},
    ]
    _, _, cont, _, _, status = gemini_verifier_service.calculate_metrics_and_integrity(f_contradicted, [])
    assert cont == 1
    assert status == OverallIntegrityStatus.MISLEADING_CLAIMS_DETECTED.value

    # 2. Partly true without contradiction -> DISCREPANCIES_FOUND
    f_partly = [
        {"classification": "SUPPORTED"},
        {"classification": "PARTLY_TRUE"},
    ]
    _, part, _, _, _, status = gemini_verifier_service.calculate_metrics_and_integrity(f_partly, [])
    assert part == 1
    assert status == OverallIntegrityStatus.DISCREPANCIES_FOUND.value

    # 3. Unclear present -> NEEDS_REVIEW
    f_unclear = [
        {"classification": "SUPPORTED"},
        {"classification": "UNCLEAR"},
    ]
    _, _, _, _, unc, status = gemini_verifier_service.calculate_metrics_and_integrity(f_unclear, [])
    assert unc == 1
    assert status == OverallIntegrityStatus.NEEDS_REVIEW.value

    # 4. All supported -> VERIFIED
    f_clean = [{"classification": "SUPPORTED"}, {"classification": "SUPPORTED"}]
    sup, _, _, _, _, status = gemini_verifier_service.calculate_metrics_and_integrity(f_clean, [])
    assert sup == 2
    assert status == OverallIntegrityStatus.VERIFIED.value


# ==============================================================================
# 2. API Integration Tests
# ==============================================================================

async def setup_verification_environment(client: httpx.AsyncClient):
    """Sets up authority, agent, customer A, customer B, policy, and completed sales session."""
    settings = get_settings()
    pwd = "SecureVerificationPassword123!"

    # 1. Authority
    auth_email = f"auth_ver_{uuid.uuid4().hex[:6]}@example.com"
    await client.post(
        "/api/v1/auth/bootstrap-authority",
        json={
            "email": auth_email,
            "password": pwd,
            "full_name": "Verification Authority",
            "bootstrap_secret": settings.AUTHORITY_BOOTSTRAP_SECRET,
        },
    )
    auth_login = await client.post("/api/v1/auth/login", json={"email": auth_email, "password": pwd})
    auth_token = auth_login.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # 2. Agent
    agent_email = f"agent_ver_{uuid.uuid4().hex[:6]}@example.com"
    agent_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": agent_email, "password": pwd, "full_name": "Verification Agent", "role": "INSURANCE_AGENT"},
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

    # 3. Customer A
    cust_a_email = f"cust_a_ver_{uuid.uuid4().hex[:6]}@example.com"
    cust_a_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": cust_a_email, "password": pwd, "full_name": "Customer Alice", "role": "CUSTOMER"},
    )
    cust_a_id = cust_a_signup.json()["id"]
    raw_token_a = [m for m in EmailService.sent_messages if m.to_email == cust_a_email][-1].token
    await client.post("/api/v1/auth/verify-email", json={"token": raw_token_a})
    cust_a_login = await client.post("/api/v1/auth/login", json={"email": cust_a_email, "password": pwd})
    cust_a_token = cust_a_login.json()["access_token"]
    cust_a_headers = {"Authorization": f"Bearer {cust_a_token}"}

    # 4. Customer B (for isolation tests)
    cust_b_email = f"cust_b_ver_{uuid.uuid4().hex[:6]}@example.com"
    cust_b_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": cust_b_email, "password": pwd, "full_name": "Customer Bob", "role": "CUSTOMER"},
    )
    cust_b_id = cust_b_signup.json()["id"]
    raw_token_b = [m for m in EmailService.sent_messages if m.to_email == cust_b_email][-1].token
    await client.post("/api/v1/auth/verify-email", json={"token": raw_token_b})
    cust_b_login = await client.post("/api/v1/auth/login", json={"email": cust_b_email, "password": pwd})
    cust_b_token = cust_b_login.json()["access_token"]
    cust_b_headers = {"Authorization": f"Bearer {cust_b_token}"}

    # 5. Create Policy & Policy Version with structured terms
    policy_code = f"MED-{uuid.uuid4().hex[:4].upper()}"
    policy_res = await client.post(
        "/api/v1/policies",
        headers=auth_headers,
        json={
            "insurer_name": "CareShield Health",
            "policy_name": "Comprehensive Medical Shield",
            "policy_code": policy_code,
            "category": "MEDICAL",
            "description": "Premium health coverage with dental and inpatient benefits.",
            "coverage_limit": 1000000.0,
            "waiting_period_days": 30,
            "claim_filing_window_days": 60,
        },
    )
    policy_id = policy_res.json()["id"]

    policy_text = """
    SECTION 1: INPATIENT HOSPITALIZATION
    Clause 1.1: Inpatient hospitalization is covered up to 1,000,000 INR subject to a 30-day waiting period.
    Clause 1.2: Daycare procedures are fully covered.

    SECTION 2: DENTAL AND VISION
    Clause 2.1: Dental surgery is covered up to 50,000 INR per policy year.
    Clause 2.2: Routine cosmetic dentistry is strictly excluded.

    SECTION 3: GENERAL EXCLUSIONS
    Clause 3.1: Cosmetic procedures and experimental treatments are excluded from coverage.
    Clause 3.2: Pre-existing conditions are not covered during the first 24 months.
    """

    version_res = await client.post(
        f"/api/v1/policies/{policy_id}/versions",
        headers=auth_headers,
        json={
            "version_number": 1,
            "document_storage_ref": "https://storage.example.com/policies/med_shield_v1.pdf",
            "document_checksum": "b" * 64,
            "effective_date": "2026-01-01",
            "terms_json": {"text": policy_text},
        },
    )
    version_id = version_res.json()["id"]

    await client.post(
        f"/api/v1/policies/{policy_id}/versions/{version_id}/publish",
        headers=auth_headers,
    )

    # 6. Create Sales Session
    transcript = (
        "Agent: Hello Alice, welcome to CareShield! Let me explain your Medical Shield benefits.\n"
        "Customer: Great, is dental surgery covered?\n"
        "Agent: Yes absolutely, dental surgery is covered up to 50,000 INR per policy year.\n"
        "Customer: What about cosmetic surgery for my nose?\n"
        "Agent: Don't worry, cosmetic procedures are completely covered under our VIP plan.\n"
        "Customer: Is hospitalization immediate?\n"
        "Agent: Hospitalization is covered immediately from day one without waiting.\n"
        "Customer: Do I get free airport lounge access?\n"
        "Agent: Yes, we provide free airport lounge access with this policy.\n"
        "Customer: What about alternative homeopathic medicine?\n"
        "Agent: Well, that might be covered depending on doctor notes."
    )

    session_res = await client.post(
        "/api/v1/sales-sessions",
        headers=agent_headers,
        json={
            "customer_id": cust_a_id,
            "policy_id": policy_id,
            "policy_version_id": version_id,
            "audio_storage_ref": "cloudinary://vachan/sales/alice_session.mp3",
            "audio_mime_type": "audio/mpeg",
            "audio_file_size_bytes": 2048576,
            "duration_seconds": 240,
            "audio_checksum": "c" * 64,
            "customer_consent": True,
            "consent_notes": "Consent confirmed.",
        },
    )
    session_id = session_res.json()["id"]

    # Mark session as COMPLETED with the transcript
    async with get_db_connection() as conn:
        await sales_session_repo.update_transcription_success(
            conn=conn,
            session_id=session_id,
            transcript=transcript,
            detected_language="en",
            word_segments=[],
            speaker_diarization=[],
            provider_model="scribe_v2",
        )

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
        "session_id": session_id,
        "transcript": transcript,
        "policy_text": policy_text,
    }


@pytest.mark.asyncio
async def test_end_to_end_policy_verification_with_5_categories(async_client: httpx.AsyncClient):
    """
    Tests complete verification run:
    - Mocks Gemini response returning all 5 categories (SUPPORTED, PARTLY_TRUE, CONTRADICTED, NOT_IN_POLICY, UNCLEAR).
    - Checks grounding validation on quotes.
    - Asserts metrics and MISLEADING_CLAIMS_DETECTED overall status.
    """
    env = await setup_verification_environment(async_client)
    session_id = env["session_id"]

    mock_gemini_payload = {
        "summary": "Audited sales session against Comprehensive Medical Shield policy terms.",
        "findings": [
            {
                "promise_text": "Dental surgery is covered up to 50,000 INR",
                "transcript_quote": "dental surgery is covered up to 50,000 INR per policy year",
                "speaker_label": "Agent",
                "classification": "SUPPORTED",
                "policy_excerpt": "Dental surgery is covered up to 50,000 INR per policy year",
                "page_number": 1,
                "section_heading": "SECTION 2: DENTAL AND VISION",
                "explanation": "Clause 2.1 explicitly confirms 50,000 INR limit.",
                "confidence": 0.99,
            },
            {
                "promise_text": "Hospitalization covered immediately from day one",
                "transcript_quote": "Hospitalization is covered immediately from day one without waiting",
                "speaker_label": "Agent",
                "classification": "PARTLY_TRUE",
                "policy_excerpt": "Inpatient hospitalization is covered up to 1,000,000 INR subject to a 30-day waiting period",
                "page_number": 1,
                "section_heading": "SECTION 1: INPATIENT HOSPITALIZATION",
                "explanation": "Hospitalization is covered, but omits mandatory 30-day waiting period.",
                "confidence": 0.95,
            },
            {
                "promise_text": "Cosmetic procedures are completely covered",
                "transcript_quote": "cosmetic procedures are completely covered under our VIP plan",
                "speaker_label": "Agent",
                "classification": "CONTRADICTED",
                "policy_excerpt": "Cosmetic procedures and experimental treatments are excluded from coverage",
                "page_number": 1,
                "section_heading": "SECTION 3: GENERAL EXCLUSIONS",
                "explanation": "Policy explicitly excludes cosmetic procedures in Clause 3.1.",
                "confidence": 0.99,
            },
            {
                "promise_text": "Free airport lounge access provided",
                "transcript_quote": "we provide free airport lounge access with this policy",
                "speaker_label": "Agent",
                "classification": "NOT_IN_POLICY",
                "policy_excerpt": None,
                "page_number": None,
                "section_heading": None,
                "explanation": "No mention of travel or airport lounge benefits in health policy.",
                "confidence": 0.92,
            },
            {
                "promise_text": "Alternative homeopathic medicine might be covered",
                "transcript_quote": "that might be covered depending on doctor notes",
                "speaker_label": "Agent",
                "classification": "UNCLEAR",
                "policy_excerpt": None,
                "page_number": None,
                "section_heading": None,
                "explanation": "Policy does not clearly define homeopathic coverage terms.",
                "confidence": 0.75,
            },
        ],
    }

    with patch.object(
        gemini_verifier_service,
        "_call_gemini_api",
        new=AsyncMock(return_value=mock_gemini_payload),
    ):
        res = await async_client.post(
            f"/api/v1/sales-sessions/{session_id}/verify-policy",
            headers=env["agent_headers"],
        )
        assert res.status_code == 200
        report = res.json()

        assert report["sales_session_id"] == session_id
        assert report["report_version"] == 1
        assert report["status"] == "COMPLETED"
        assert report["overall_integrity_status"] == OverallIntegrityStatus.MISLEADING_CLAIMS_DETECTED.value
        assert report["supported_count"] == 1
        assert report["partly_true_count"] == 1
        assert report["contradicted_count"] == 1
        assert report["not_in_policy_count"] == 1
        assert report["unclear_count"] == 1
        assert len(report["findings"]) == 5

        # Verify all findings are GROUNDED
        for f in report["findings"][:3]:
            assert f["validation_status"] == ValidationStatus.GROUNDED.value


@pytest.mark.asyncio
async def test_reanalyze_verification_increments_version(async_client: httpx.AsyncClient):
    """
    Tests that reanalyzing creates a new immutable version without modifying or deleting version 1.
    """
    env = await setup_verification_environment(async_client)
    session_id = env["session_id"]

    mock_gemini_payload = {
        "summary": "Initial verification run.",
        "findings": [
            {
                "promise_text": "Dental surgery covered",
                "transcript_quote": "dental surgery is covered up to 50,000 INR per policy year",
                "speaker_label": "Agent",
                "classification": "SUPPORTED",
                "policy_excerpt": "Dental surgery is covered up to 50,000 INR per policy year",
                "explanation": "Confirmed.",
                "confidence": 0.99,
            }
        ],
    }

    with patch.object(
        gemini_verifier_service,
        "_call_gemini_api",
        new=AsyncMock(return_value=mock_gemini_payload),
    ):
        # 1. Initial verification -> version 1
        res1 = await async_client.post(
            f"/api/v1/sales-sessions/{session_id}/verify-policy",
            headers=env["agent_headers"],
        )
        assert res1.status_code == 200
        report_v1 = res1.json()
        assert report_v1["report_version"] == 1
        report_id_v1 = report_v1["id"]

        # 2. Reanalyze -> version 2
        res2 = await async_client.post(
            f"/api/v1/verification-reports/{report_id_v1}/reanalyze",
            headers=env["agent_headers"],
            json={"reason": "Customer contested finding after reviewing recording."},
        )
        assert res2.status_code == 200
        report_v2 = res2.json()
        assert report_v2["report_version"] == 2
        assert report_v2["id"] != report_id_v1

        # 3. Retrieve all versions
        res_all = await async_client.get(
            f"/api/v1/sales-sessions/{session_id}/verification?all_versions=true",
            headers=env["agent_headers"],
        )
        assert res_all.status_code == 200
        versions = res_all.json()
        assert len(versions) == 2
        version_nums = [v["report_version"] for v in versions]
        assert 1 in version_nums and 2 in version_nums


@pytest.mark.asyncio
async def test_rbac_access_isolation_on_reports(async_client: httpx.AsyncClient):
    """
    Tests that Customer B cannot view Customer A's verification reports,
    while Customer A, Agent, and Authority can access them.
    """
    env = await setup_verification_environment(async_client)
    session_id = env["session_id"]

    mock_gemini_payload = {
        "summary": "RBAC verification test.",
        "findings": [],
    }

    with patch.object(
        gemini_verifier_service,
        "_call_gemini_api",
        new=AsyncMock(return_value=mock_gemini_payload),
    ):
        # Run verification
        init_res = await async_client.post(
            f"/api/v1/sales-sessions/{session_id}/verify-policy",
            headers=env["agent_headers"],
        )
        report_id = init_res.json()["id"]

        # 1. Customer B attempts to get report -> 404 (isolation)
        unauth_res = await async_client.get(
            f"/api/v1/verification-reports/{report_id}",
            headers=env["cust_b_headers"],
        )
        assert unauth_res.status_code == 404

        # 2. Customer A can view own report
        cust_a_res = await async_client.get(
            f"/api/v1/verification-reports/{report_id}",
            headers=env["cust_a_headers"],
        )
        assert cust_a_res.status_code == 200

        # 3. Authority can view report
        auth_res = await async_client.get(
            f"/api/v1/verification-reports/{report_id}",
            headers=env["auth_headers"],
        )
        assert auth_res.status_code == 200


@pytest.mark.asyncio
async def test_cannot_verify_uncompleted_sales_session(async_client: httpx.AsyncClient):
    """
    Tests that attempting to verify a session whose transcription is PENDING fails.
    """
    env = await setup_verification_environment(async_client)

    # Create session with PENDING status (no completed transcript)
    res = await async_client.post(
        "/api/v1/sales-sessions",
        headers=env["agent_headers"],
        json={
            "customer_id": env["cust_a_id"],
            "policy_id": env["policy_id"],
            "policy_version_id": env["version_id"],
            "audio_storage_ref": "cloudinary://vachan/sales/pending_session.mp3",
            "audio_mime_type": "audio/mpeg",
            "audio_file_size_bytes": 1024,
            "duration_seconds": 60,
            "audio_checksum": "d" * 64,
            "customer_consent": True,
        },
    )
    pending_session_id = res.json()["id"]

    # Verify attempt should fail
    verify_res = await async_client.post(
        f"/api/v1/sales-sessions/{pending_session_id}/verify-policy",
        headers=env["agent_headers"],
    )
    # Status code is 422 ValidationException
    assert verify_res.status_code == 422
    err_body = verify_res.json()
    err_msg = (err_body.get("error") or err_body.get("detail") or "").lower()
    assert "transcription must be completed" in err_msg

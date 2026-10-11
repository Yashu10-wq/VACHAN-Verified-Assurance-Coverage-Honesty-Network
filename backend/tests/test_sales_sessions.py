"""
Automated test suite for Phase 5: ElevenLabs Speech-to-Text & Sales Sessions.
Tests sales conversation recording sessions, affirmative customer recording consent,
Cloudinary audio validation, mocked ElevenLabs STT processing, diarization handling,
duplicate job prevention, and RBAC isolation.
"""

from unittest.mock import patch
import uuid
import httpx
import pytest

from app.core.config import get_settings
from app.services.elevenlabs_stt import TranscriptionResult
from app.services.email_service import EmailService


async def setup_sales_test_environment(client: httpx.AsyncClient):
    """Sets up active authority, active agent, customer, and confirmed registration."""
    settings = get_settings()
    pwd = "SecureSalesPassword123!"

    # 1. Authority
    auth_email = f"auth_sales_{uuid.uuid4().hex[:6]}@example.com"
    await client.post(
        "/api/v1/auth/bootstrap-authority",
        json={
            "email": auth_email,
            "password": pwd,
            "full_name": "Sales Authority Admin",
            "bootstrap_secret": settings.AUTHORITY_BOOTSTRAP_SECRET,
        },
    )
    auth_login = await client.post("/api/v1/auth/login", json={"email": auth_email, "password": pwd})
    auth_token = auth_login.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # 2. Agent
    agent_email = f"agent_sales_{uuid.uuid4().hex[:6]}@example.com"
    agent_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": agent_email, "password": pwd, "full_name": "Sales Field Agent", "role": "INSURANCE_AGENT"},
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
    cust_a_email = f"cust_a_sales_{uuid.uuid4().hex[:6]}@example.com"
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
    cust_b_email = f"cust_b_sales_{uuid.uuid4().hex[:6]}@example.com"
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

    return {
        "auth_headers": auth_headers,
        "agent_headers": agent_headers,
        "agent_id": agent_id,
        "cust_a_headers": cust_a_headers,
        "cust_a_id": cust_a_id,
        "cust_b_headers": cust_b_headers,
        "cust_b_id": cust_b_id,
    }


@pytest.mark.asyncio
async def test_sales_session_creation_and_consent_validation(async_client: httpx.AsyncClient):
    """
    Tests sales session creation:
    - Agent creates session with affirmative consent.
    - Customer cannot initiate session creation (403 Forbidden).
    - Invalid audio MIME type rejection (422).
    """
    env = await setup_sales_test_environment(async_client)

    # 1. Successful session creation
    session_payload = {
        "customer_id": env["cust_a_id"],
        "audio_storage_ref": "cloudinary://vachan/sales/session_001.mp3",
        "audio_mime_type": "audio/mpeg",
        "audio_file_size_bytes": 1048576,  # 1MB
        "duration_seconds": 180,
        "audio_checksum": "a" * 64,
        "customer_consent": True,
        "consent_notes": "Customer consented verbally at start of recording.",
    }
    res = await async_client.post("/api/v1/sales-sessions", headers=env["agent_headers"], json=session_payload)
    assert res.status_code == 201
    session = res.json()
    assert session["status"] == "PENDING"
    assert session["customer_consent"] is True
    assert session["agent_id"] == env["agent_id"]

    # 2. Customer attempting to create sales session -> 403 Forbidden
    cust_attempt = await async_client.post("/api/v1/sales-sessions", headers=env["cust_a_headers"], json=session_payload)
    assert cust_attempt.status_code == 403

    # 3. Invalid audio MIME rejection
    bad_payload = dict(session_payload, audio_mime_type="video/mp4")
    bad_res = await async_client.post("/api/v1/sales-sessions", headers=env["agent_headers"], json=bad_payload)
    assert bad_res.status_code == 422


@pytest.mark.asyncio
async def test_transcription_consent_enforcement(async_client: httpx.AsyncClient):
    """
    Tests that transcription cannot be started if customer consent is missing or False.
    """
    env = await setup_sales_test_environment(async_client)

    # Create session WITHOUT customer consent
    res = await async_client.post(
        "/api/v1/sales-sessions",
        headers=env["agent_headers"],
        json={
            "customer_id": env["cust_a_id"],
            "audio_storage_ref": "cloudinary://vachan/sales/no_consent.mp3",
            "audio_mime_type": "audio/mpeg",
            "audio_file_size_bytes": 500000,
            "audio_checksum": "b" * 64,
            "customer_consent": False,
        },
    )
    assert res.status_code == 201
    session_id = res.json()["id"]

    # Attempt to transcribe without consent -> 409 Conflict
    tx_res = await async_client.post(f"/api/v1/sales-sessions/{session_id}/transcribe", headers=env["agent_headers"])
    assert tx_res.status_code == 409
    assert "Customer consent is missing or declined" in tx_res.json()["error"]


@pytest.mark.asyncio
async def test_successful_multilingual_transcription_flow(async_client: httpx.AsyncClient):
    """
    Tests speech-to-text execution with mocked ElevenLabs Scribe API:
    - Mocked transcript with mixed Hindi/English speech.
    - Word segments and speaker diarization.
    - Transcript retrieval by authorized customer and agent.
    - Duplicate transcription returns existing result without re-processing.
    """
    env = await setup_sales_test_environment(async_client)

    # Create consented session
    res = await async_client.post(
        "/api/v1/sales-sessions",
        headers=env["agent_headers"],
        json={
            "customer_id": env["cust_a_id"],
            "audio_storage_ref": "cloudinary://vachan/sales/multilingual_convo.mp3",
            "audio_mime_type": "audio/mpeg",
            "audio_file_size_bytes": 1024000,
            "audio_checksum": "c" * 64,
            "customer_consent": True,
        },
    )
    session_id = res.json()["id"]

    mock_result = TranscriptionResult(
        transcript="Namaste sir, aapka policy premium yearly 25000 rupees rahega, full cashless coverage included.",
        detected_language="hi",
        word_segments=[
            {"text": "Namaste", "start": 0.1, "end": 0.6, "speaker_id": "agent", "type": "word"},
            {"text": "sir", "start": 0.7, "end": 1.0, "speaker_id": "agent", "type": "word"},
            {"text": "premium", "start": 1.2, "end": 1.8, "speaker_id": "agent", "type": "word"},
        ],
        speaker_diarization=[
            {"speaker_id": "agent", "start": 0.0, "end": 5.0},
            {"speaker_id": "customer", "start": 5.1, "end": 8.0},
        ],
        provider_model="scribe_v2",
    )

    with patch("app.services.elevenlabs_stt.elevenlabs_stt_service.transcribe_audio", return_value=mock_result):
        tx_res = await async_client.post(f"/api/v1/sales-sessions/{session_id}/transcribe", headers=env["agent_headers"])
        assert tx_res.status_code == 200
        data = tx_res.json()
        assert data["status"] == "COMPLETED"
        assert "Namaste sir" in data["transcript"]

    # 1. Retrieve full transcript as Customer A
    t_res = await async_client.get(f"/api/v1/sales-sessions/{session_id}/transcript", headers=env["cust_a_headers"])
    assert t_res.status_code == 200
    transcript_data = t_res.json()
    assert transcript_data["detected_language"] == "hi"
    assert len(transcript_data["word_segments"]) == 3
    assert len(transcript_data["speaker_diarization"]) == 2

    # 2. Duplicate transcription request returns existing result without re-transcribing
    dup_res = await async_client.post(f"/api/v1/sales-sessions/{session_id}/transcribe", headers=env["agent_headers"])
    assert dup_res.status_code == 200
    assert dup_res.json()["message"] == "Transcription already completed for this session."


@pytest.mark.asyncio
async def test_session_rbac_data_isolation(async_client: httpx.AsyncClient):
    """
    Tests security isolation:
    - Customer A cannot access Customer B's sessions or transcripts (404).
    - Customer cannot initiate transcription (403).
    """
    env = await setup_sales_test_environment(async_client)

    # Session for Customer A
    res = await async_client.post(
        "/api/v1/sales-sessions",
        headers=env["agent_headers"],
        json={
            "customer_id": env["cust_a_id"],
            "audio_storage_ref": "cloudinary://vachan/sales/private_audio.mp3",
            "audio_mime_type": "audio/mpeg",
            "audio_file_size_bytes": 1024000,
            "audio_checksum": "d" * 64,
            "customer_consent": True,
        },
    )
    session_id = res.json()["id"]

    # Customer B attempts to view Customer A's session -> 404 Not Found
    b_res = await async_client.get(f"/api/v1/sales-sessions/{session_id}", headers=env["cust_b_headers"])
    assert b_res.status_code == 404

    # Customer A attempts to trigger transcription -> 403 Forbidden
    cust_tx = await async_client.post(f"/api/v1/sales-sessions/{session_id}/transcribe", headers=env["cust_a_headers"])
    assert cust_tx.status_code == 403

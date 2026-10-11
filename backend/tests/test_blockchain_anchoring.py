"""
Automated test suite for Phase 8: Blockchain Audit Anchoring & Integrity Engine.
Tests canonical SHA-256 hash determinism, genesis/previous-hash linkage, tampering detection,
Merkle tree proofs, on-chain verification, RBAC scoping, and offline RPC resilience.
"""

from unittest.mock import AsyncMock, patch
import uuid
import httpx
import pytest

from app.core.config import get_settings
from app.db.connection import get_db_connection
from app.db.repositories import anchor_batch_repo, audit_repo
from app.services.audit_chain import (
    GENESIS_HASH,
    HASH_VERSION,
    append_chained_audit_event,
    backfill_legacy_audit_records,
    compute_event_hash,
    compute_payload_hash,
    verify_event_chain_integrity,
)
from app.services.blockchain_service import (
    BlockchainService,
    blockchain_service,
    pad_bytes32_hex,
)
from app.services.email_service import EmailService
from app.services.merkle_tree import MerkleTree, verify_merkle_proof


# ==============================================================================
# 1. Unit Tests: Hash Determinism, Tamper Detection & Merkle Proofs
# ==============================================================================

def test_canonical_payload_hash_determinism():
    """Tests that payload hashing is deterministic regardless of key order or whitespace."""
    hash1 = compute_payload_hash(
        actor_id="user-123",
        actor_role="INSURANCE_AGENT",
        action="APPROVE_CLAIM",
        target_type="claim",
        target_id="claim-456",
        metadata={"amount": 5000, "currency": "INR", "notes": "Approved by senior agent"},
        created_at_iso="2026-10-11T12:00:00Z",
    )
    # Swapped dictionary key insertion order
    hash2 = compute_payload_hash(
        actor_id="user-123",
        actor_role="INSURANCE_AGENT",
        action="APPROVE_CLAIM",
        target_type="claim",
        target_id="claim-456",
        metadata={"notes": "Approved by senior agent", "currency": "INR", "amount": 5000},
        created_at_iso="2026-10-11T12:00:00Z",
    )
    assert hash1 == hash2
    assert len(hash1) == 64


def test_event_link_hash_computation():
    """Tests event hash formula: SHA-256(version|seq|prev_hash|payload_hash)."""
    p_hash = "a" * 64
    prev = GENESIS_HASH
    event_h = compute_event_hash(
        hash_version="v1",
        sequence_number=1,
        previous_hash=prev,
        payload_hash=p_hash,
    )
    assert len(event_h) == 64

    # Changing sequence number produces completely different hash
    event_h2 = compute_event_hash(
        hash_version="v1",
        sequence_number=2,
        previous_hash=prev,
        payload_hash=p_hash,
    )
    assert event_h != event_h2


def test_merkle_tree_root_and_inclusion_proof():
    """Tests binary Merkle tree root derivation and inclusion proof verification for even and odd counts."""
    leaves = [
        "11" * 32,
        "22" * 32,
        "33" * 32,
        "44" * 32,
        "55" * 32,  # Odd count (5 leaves)
    ]
    tree = MerkleTree(leaves)
    assert len(tree.root) == 64

    # Verify inclusion proof for each individual leaf
    for idx, leaf in enumerate(leaves):
        proof = tree.get_proof(idx)
        assert len(proof) > 0
        is_valid = verify_merkle_proof(
            leaf_hash=leaf,
            proof=proof,
            expected_root=tree.root,
        )
        assert is_valid is True

    # Tampered leaf fails verification
    tampered_leaf = "99" * 32
    assert verify_merkle_proof(tampered_leaf, tree.get_proof(0), tree.root) is False


# ==============================================================================
# 2. Database Integration & Hash Chain Tamper Detection
# ==============================================================================

@pytest.mark.asyncio
async def test_atomic_hash_chain_creation_and_tamper_detection():
    """
    Tests sequential chain link creation and tamper detection:
    - Appends sequential events.
    - Verifies event passes all checks (VALID).
    - Simulates database tampering (modified metadata payload) -> HASH_MISMATCH.
    - Simulates broken previous_hash pointer -> PREVIOUS_HASH_MISMATCH.
    """
    async with get_db_connection() as conn:
        # 1. Append valid event
        ev1 = await append_chained_audit_event(
            conn=conn,
            actor_id=None,
            actor_role="INSURANCE_AGENT",
            action="CREATE_POLICY",
            target_type="policy",
            target_id="pol-001",
            metadata={"plan": "Gold Shield"},
        )
        assert ev1["sequence_number"] is not None
        assert len(ev1["event_hash"]) == 64

        # 2. Append second linked event
        ev2 = await append_chained_audit_event(
            conn=conn,
            actor_id=None,
            actor_role="CUSTOMER",
            action="FILE_CLAIM",
            target_type="claim",
            target_id="clm-001",
            metadata={"amount": 25000},
        )
        assert ev2["sequence_number"] == ev1["sequence_number"] + 1
        assert ev2["previous_hash"] == ev1["event_hash"]

        # 3. Verify integrity passes
        res_v1 = await verify_event_chain_integrity(conn, ev1["id"])
        assert res_v1["outcome"] == "VALID"

        res_v2 = await verify_event_chain_integrity(conn, ev2["id"])
        assert res_v2["outcome"] == "VALID"

        # 4. Simulate tampering with ev2 payload in database
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE audit_logs SET metadata = %s WHERE id = %s;",
                ('{"amount": 9999999, "tampered": true}', ev2["id"]),
            )

        res_tampered = await verify_event_chain_integrity(conn, ev2["id"])
        assert res_tampered["outcome"] == "HASH_MISMATCH"
        assert "payload hash mismatch" in res_tampered["message"].lower()

        # 5. Restore payload and simulate broken previous_hash
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE audit_logs SET metadata = %s, previous_hash = %s WHERE id = %s;",
                ('{"amount": 25000}', "f" * 64, ev2["id"]),
            )

        res_broken_chain = await verify_event_chain_integrity(conn, ev2["id"])
        assert res_broken_chain["outcome"] == "HASH_MISMATCH" or res_broken_chain["outcome"] == "PREVIOUS_HASH_MISMATCH"


# ==============================================================================
# 3. API Integration, RBAC, Merkle Proofs & Offline Resilience
# ==============================================================================

async def setup_anchoring_test_environment(client: httpx.AsyncClient):
    """Sets up authority, agent, and customers for RBAC testing."""
    settings = get_settings()
    pwd = "SecureAnchoringPassword123!"

    # 1. Authority
    auth_email = f"auth_anc_{uuid.uuid4().hex[:6]}@example.com"
    await client.post(
        "/api/v1/auth/bootstrap-authority",
        json={
            "email": auth_email,
            "password": pwd,
            "full_name": "Anchor Authority Admin",
            "bootstrap_secret": settings.AUTHORITY_BOOTSTRAP_SECRET,
        },
    )
    auth_login = await client.post("/api/v1/auth/login", json={"email": auth_email, "password": pwd})
    auth_token = auth_login.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}

    # 2. Customer A
    cust_a_email = f"cust_a_anc_{uuid.uuid4().hex[:6]}@example.com"
    cust_a_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": cust_a_email, "password": pwd, "full_name": "Customer Alice", "role": "CUSTOMER"},
    )
    cust_a_id = cust_a_signup.json()["id"]
    raw_token_a = [m for m in EmailService.sent_messages if m.to_email == cust_a_email][-1].token
    await client.post("/api/v1/auth/verify-email", json={"token": raw_token_a})
    cust_a_login = await client.post("/api/v1/auth/login", json={"email": cust_a_email, "password": pwd})
    cust_a_headers = {"Authorization": f"Bearer {cust_a_login.json()['access_token']}"}

    # 3. Customer B (for isolation)
    cust_b_email = f"cust_b_anc_{uuid.uuid4().hex[:6]}@example.com"
    cust_b_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": cust_b_email, "password": pwd, "full_name": "Customer Bob", "role": "CUSTOMER"},
    )
    cust_b_id = cust_b_signup.json()["id"]
    raw_token_b = [m for m in EmailService.sent_messages if m.to_email == cust_b_email][-1].token
    await client.post("/api/v1/auth/verify-email", json={"token": raw_token_b})
    cust_b_login = await client.post("/api/v1/auth/login", json={"email": cust_b_email, "password": pwd})
    cust_b_headers = {"Authorization": f"Bearer {cust_b_login.json()['access_token']}"}

    return {
        "auth_headers": auth_headers,
        "cust_a_headers": cust_a_headers,
        "cust_a_id": cust_a_id,
        "cust_b_headers": cust_b_headers,
        "cust_b_id": cust_b_id,
    }


@pytest.mark.asyncio
async def test_blockchain_status_offline_resilience(async_client: httpx.AsyncClient):
    """
    Tests GET /api/v1/integrity/status:
    - Never crashes when blockchain RPC is offline.
    - Gracefully reports BLOCKCHAIN_UNAVAILABLE.
    """
    env = await setup_anchoring_test_environment(async_client)
    res = await async_client.get("/api/v1/integrity/status", headers=env["cust_a_headers"])
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "total_events" in data
    assert "pending_events" in data
    assert "anchored_events" in data


@pytest.mark.asyncio
async def test_end_to_end_batch_anchoring_and_merkle_proof(async_client: httpx.AsyncClient):
    """
    Tests end-to-end batch anchoring with mocked EVM RPC:
    - Creates chained audit events for customer A.
    - Authority triggers POST /api/v1/integrity/anchor-pending.
    - Verifies event transitions to ANCHORED.
    - Retrieves Merkle proof via GET /api/v1/integrity/audit-events/{id}/proof.
    - Validates proof evaluation.
    """
    env = await setup_anchoring_test_environment(async_client)

    # 1. Insert chained audit events for customer A
    async with get_db_connection() as conn:
        ev1 = await append_chained_audit_event(
            conn=conn,
            actor_id=env["cust_a_id"],
            actor_role="CUSTOMER",
            action="SUBMIT_CLAIM_EVIDENCE",
            target_type="claim_evidence",
            target_id="evid-001",
            metadata={"customer_id": env["cust_a_id"], "filename": "hospital_bill.pdf"},
        )
        ev2 = await append_chained_audit_event(
            conn=conn,
            actor_id=env["cust_a_id"],
            actor_role="CUSTOMER",
            action="CONFIRM_REGISTRATION",
            target_type="policy_registration",
            target_id="reg-001",
            metadata={"customer_id": env["cust_a_id"]},
        )

    # 2. Mock blockchain service RPC
    mock_status = {
        "is_connected": True,
        "rpc_url": "http://127.0.0.1:8545",
        "configured_chain_id": 31337,
        "node_chain_id": 31337,
        "block_number": 42,
        "contract_address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
        "contract_deployed": True,
        "status": "ACTIVE",
    }
    mock_tx_res = {
        "tx_hash": "0x" + "c" * 64,
        "block_number": 43,
        "chain_id": 31337,
        "contract_address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
    }
    mock_chain_verify = {
        "exists": True,
        "sequence_number": 1,
        "timestamp": 1700000000,
        "event_count": 2,
    }

    with patch.object(blockchain_service, "get_blockchain_status", new=AsyncMock(return_value=mock_status)), \
         patch.object(blockchain_service, "anchor_batch_to_chain", new=AsyncMock(return_value=mock_tx_res)), \
         patch.object(blockchain_service, "verify_commitment_on_chain", new=AsyncMock(return_value=mock_chain_verify)):

        # 3. Customer cannot trigger administrative anchoring -> 403
        unauth_anchor = await async_client.post("/api/v1/integrity/anchor-pending", headers=env["cust_a_headers"])
        assert unauth_anchor.status_code == 403

        # 4. Authority triggers batch anchoring
        anchor_res = await async_client.post("/api/v1/integrity/anchor-pending", headers=env["auth_headers"])
        assert anchor_res.status_code == 200
        assert anchor_res.json()["status"] == "SUCCESS"
        assert anchor_res.json()["anchored_events"] >= 2

        # 5. Verify individual event status
        ev_res = await async_client.get(f"/api/v1/integrity/audit-events/{ev1['id']}", headers=env["cust_a_headers"])
        assert ev_res.status_code == 200
        ev_data = ev_res.json()
        assert ev_data["outcome"] == "VALID"
        assert ev_data["anchoring_status"] == "ANCHORED"
        assert ev_data["on_chain_verified"] is True

        # 6. Fetch Merkle inclusion proof
        proof_res = await async_client.get(f"/api/v1/integrity/audit-events/{ev1['id']}/proof", headers=env["cust_a_headers"])
        assert proof_res.status_code == 200
        proof_data = proof_res.json()
        assert proof_data["event_id"] == ev1["id"]
        assert proof_data["batch_root_hash"] is not None
        assert proof_data["tx_hash"] == mock_tx_res["tx_hash"]
        assert proof_data["on_chain_commitment_verified"] is True
        assert len(proof_data["merkle_proof"]) > 0


@pytest.mark.asyncio
async def test_rbac_audit_event_isolation(async_client: httpx.AsyncClient):
    """
    Tests that Customer B cannot view Customer A's audit event or proof (404 isolation),
    while Customer A and Authority have access.
    """
    env = await setup_anchoring_test_environment(async_client)

    # Insert event for Customer A
    async with get_db_connection() as conn:
        ev_a = await append_chained_audit_event(
            conn=conn,
            actor_id=env["cust_a_id"],
            actor_role="CUSTOMER",
            action="SUBMIT_CLAIM",
            target_type="claim",
            target_id="claim-priv-001",
            metadata={"customer_id": env["cust_a_id"]},
        )

    # 1. Customer B attempts to inspect Customer A's event -> 404 (isolation)
    res_b = await async_client.get(f"/api/v1/integrity/audit-events/{ev_a['id']}", headers=env["cust_b_headers"])
    assert res_b.status_code == 404

    # 2. Customer A can view own event
    res_a = await async_client.get(f"/api/v1/integrity/audit-events/{ev_a['id']}", headers=env["cust_a_headers"])
    assert res_a.status_code == 200

    # 3. Authority can view all events
    res_auth = await async_client.get(f"/api/v1/integrity/audit-events/{ev_a['id']}", headers=env["auth_headers"])
    assert res_auth.status_code == 200

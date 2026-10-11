"""
Pydantic validation schemas for Blockchain Audit Anchoring & Integrity Engine.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MerkleProofStep(BaseModel):
    """Step in a cryptographic Merkle audit inclusion proof."""
    position: str = Field(description="'left' or 'right' indicating sibling positioning")
    hash: str = Field(description="32-byte hexadecimal sibling hash")


class BlockchainStatusResponse(BaseModel):
    """Integrity and blockchain connectivity status."""
    is_connected: bool
    rpc_url: str
    configured_chain_id: int
    node_chain_id: Optional[int] = None
    block_number: Optional[int] = None
    contract_address: Optional[str] = None
    contract_deployed: bool
    status: str
    total_events: int = 0
    unchained_events: int = 0
    pending_events: int = 0
    batched_events: int = 0
    anchored_events: int = 0
    failed_events: int = 0


class AuditEventVerificationResponse(BaseModel):
    """Cryptographic verification of an individual audit event."""
    event_id: str
    outcome: str = Field(description="VALID, HASH_MISMATCH, PREVIOUS_HASH_MISMATCH, ANCHOR_PENDING, NEEDS_REVIEW, etc.")
    message: str
    sequence_number: Optional[int] = None
    event_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    payload_hash: Optional[str] = None
    anchoring_status: Optional[str] = None
    batch_id: Optional[str] = None
    created_at: Optional[str] = None
    on_chain_verified: bool = False


class AuditEventProofResponse(BaseModel):
    """Merkle inclusion proof and on-chain anchor details for an audit event."""
    event_id: str
    sequence_number: int
    event_hash: str
    batch_id: str
    batch_sequence: int
    batch_root_hash: str
    leaf_index: int
    merkle_proof: List[MerkleProofStep]
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    chain_id: Optional[int] = None
    contract_address: Optional[str] = None
    on_chain_commitment_verified: bool = False
    anchored_at: Optional[str] = None


class VerifyRequest(BaseModel):
    """Batch verification request for multiple audit events."""
    event_ids: List[str] = Field(min_length=1, max_length=50, description="List of audit event UUIDs to verify (max 50)")


class AnchorPendingResponse(BaseModel):
    """Response after triggering on-chain anchoring for pending events."""
    batches_created: int
    anchored_events: int
    status: str
    message: str


class BackfillResponse(BaseModel):
    """Response after reconciling legacy unchained audit records."""
    backfilled_count: int
    message: str

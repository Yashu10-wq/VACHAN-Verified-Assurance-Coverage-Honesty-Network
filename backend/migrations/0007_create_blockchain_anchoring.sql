-- ==============================================================================
-- InsureChain VoiceGuard — Migration 0007: Blockchain Audit Anchoring
-- ==============================================================================
-- Implements a cryptographic SHA-256 audit hash chain, batch Merkle root commitments,
-- and smart contract anchoring tracking.

-- 1. Create Audit Anchor Batches Table
CREATE TABLE IF NOT EXISTS audit_anchor_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_sequence INT NOT NULL UNIQUE,
    batch_root_hash VARCHAR(66) NOT NULL,
    first_sequence_number BIGINT NOT NULL,
    last_sequence_number BIGINT NOT NULL,
    event_count INT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'SUBMITTING', 'ANCHORED', 'FAILED')
    ),
    tx_hash VARCHAR(66),
    block_number BIGINT,
    chain_id BIGINT,
    contract_address VARCHAR(42),
    anchored_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anchor_batches_status ON audit_anchor_batches(status);
CREATE INDEX IF NOT EXISTS idx_anchor_batches_sequence ON audit_anchor_batches(batch_sequence DESC);

-- 2. Create Audit Global Sequence
CREATE SEQUENCE IF NOT EXISTS audit_log_seq START WITH 1 INCREMENT BY 1;

-- 3. Extend Audit Logs with Hash-Chain and Anchoring Metadata
ALTER TABLE audit_logs
    ADD COLUMN IF NOT EXISTS sequence_number BIGINT UNIQUE,
    ADD COLUMN IF NOT EXISTS payload_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS previous_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS event_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS hash_version VARCHAR(16) NOT NULL DEFAULT 'v1',
    ADD COLUMN IF NOT EXISTS anchoring_status VARCHAR(32) NOT NULL DEFAULT 'PENDING' CHECK (
        anchoring_status IN ('PENDING', 'BATCHED', 'ANCHORED', 'FAILED')
    ),
    ADD COLUMN IF NOT EXISTS batch_id UUID REFERENCES audit_anchor_batches(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_audit_logs_sequence ON audit_logs(sequence_number);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_hash ON audit_logs(event_hash);
CREATE INDEX IF NOT EXISTS idx_audit_logs_anchoring_status ON audit_logs(anchoring_status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_batch ON audit_logs(batch_id);

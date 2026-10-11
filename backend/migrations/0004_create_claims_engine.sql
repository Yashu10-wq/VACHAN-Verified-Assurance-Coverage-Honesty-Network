-- ==============================================================================
-- InsureChain VoiceGuard — Migration 0004: Claims Engine
-- ==============================================================================
-- Relational schema for claims, secure evidence metadata, deterministic
-- eligibility assessments, and strictly audited claim lifecycle state history.

-- Allow policies to support MEDICAL as a first-class category alongside HOSPITALIZATION
ALTER TABLE policies DROP CONSTRAINT IF EXISTS policies_category_check;
ALTER TABLE policies ADD CONSTRAINT policies_category_check CHECK (category IN ('VEHICLE', 'HOSPITALIZATION', 'MEDICAL', 'GENERIC'));

-- 1. Claims Table
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    registration_id UUID NOT NULL REFERENCES policy_registrations(id) ON DELETE RESTRICT,
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE RESTRICT,
    policy_version_id UUID NOT NULL REFERENCES policy_versions(id) ON DELETE RESTRICT,
    claim_category VARCHAR(32) NOT NULL CHECK (claim_category IN ('VEHICLE', 'MEDICAL', 'GENERIC')),
    requested_amount NUMERIC(14, 2) NOT NULL CHECK (requested_amount > 0),
    incident_date DATE NOT NULL,
    submission_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    structured_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'SUBMITTED' CHECK (
        status IN (
            'SUBMITTED',
            'UNDER_REVIEW',
            'EVIDENCE_REQUESTED',
            'APPROVED',
            'REJECTED',
            'PAID'
        )
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_claims_customer ON claims (customer_id);
CREATE INDEX IF NOT EXISTS idx_claims_registration ON claims (registration_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims (status);
CREATE INDEX IF NOT EXISTS idx_claims_category ON claims (claim_category);
CREATE INDEX IF NOT EXISTS idx_claims_incident_date ON claims (incident_date);
CREATE INDEX IF NOT EXISTS idx_claims_created_at ON claims (created_at DESC);

-- 2. Evidence Metadata Table
CREATE TABLE IF NOT EXISTS claim_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    uploader_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    evidence_type VARCHAR(64) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    document_storage_ref VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes > 0),
    mime_type VARCHAR(128) NOT NULL,
    document_checksum VARCHAR(64) NOT NULL,
    analysis_status VARCHAR(32) NOT NULL DEFAULT 'PENDING' CHECK (
        analysis_status IN ('PENDING', 'PROCESSED', 'FAILED')
    ),
    resource_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_claim_evidence_claim ON claim_evidence (claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_uploader ON claim_evidence (uploader_id);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_created ON claim_evidence (created_at);

-- 3. Deterministic Eligibility Assessments Table
CREATE TABLE IF NOT EXISTS claim_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    policy_version_id UUID NOT NULL REFERENCES policy_versions(id) ON DELETE RESTRICT,
    assessment_version INT NOT NULL DEFAULT 1 CHECK (assessment_version > 0),
    overall_outcome VARCHAR(32) NOT NULL CHECK (
        overall_outcome IN ('ELIGIBLE', 'INELIGIBLE', 'NEEDS_REVIEW')
    ),
    rules_evaluated JSONB NOT NULL DEFAULT '[]'::jsonb,
    requested_amount NUMERIC(14, 2) NOT NULL,
    applicable_limit NUMERIC(14, 2) NOT NULL,
    potentially_payable_amount NUMERIC(14, 2) NOT NULL,
    excess_amount NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    missing_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    review_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    assessed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_claim_assessment_version UNIQUE (claim_id, assessment_version)
);

CREATE INDEX IF NOT EXISTS idx_claim_assessments_claim ON claim_assessments (claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_assessments_outcome ON claim_assessments (overall_outcome);

-- 4. Claim Status History and Decisions Audit Table
CREATE TABLE IF NOT EXISTS claim_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_role VARCHAR(32) NOT NULL,
    previous_status VARCHAR(32) NOT NULL,
    new_status VARCHAR(32) NOT NULL,
    reason TEXT NOT NULL,
    decision_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    audit_correlation_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_claim_status_history_claim ON claim_status_history (claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_status_history_created ON claim_status_history (created_at);

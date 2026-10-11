-- ==============================================================================
-- InsureChain VoiceGuard — Migration 0006: Policy Verification Engine
-- ==============================================================================
-- Relational schema for policy document text extractions, grounded Gemini promise
-- verification reports, structured findings, and audit trails.

-- 1. Policy Document Extractions Table
CREATE TABLE IF NOT EXISTS policy_document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_version_id UUID NOT NULL REFERENCES policy_versions(id) ON DELETE CASCADE,
    document_checksum VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'NEEDS_REVIEW')
    ),
    extracted_text TEXT,
    page_count INT NOT NULL DEFAULT 0,
    pages_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    parser_version VARCHAR(32) NOT NULL DEFAULT 'pypdf_v1',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_policy_extraction UNIQUE (policy_version_id, document_checksum)
);

CREATE INDEX IF NOT EXISTS idx_extractions_version ON policy_document_extractions (policy_version_id);
CREATE INDEX IF NOT EXISTS idx_extractions_status ON policy_document_extractions (status);

-- 2. Policy-Promise Verification Reports Table
CREATE TABLE IF NOT EXISTS verification_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sales_session_id UUID NOT NULL REFERENCES sales_sessions(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    agent_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE RESTRICT,
    policy_version_id UUID NOT NULL REFERENCES policy_versions(id) ON DELETE RESTRICT,
    transcript_checksum VARCHAR(64) NOT NULL,
    report_version INT NOT NULL DEFAULT 1 CHECK (report_version > 0),
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'NEEDS_REVIEW')
    ),
    model_identifier VARCHAR(64) NOT NULL DEFAULT 'gemini-2.5-flash',
    summary TEXT,
    overall_integrity_status VARCHAR(32) CHECK (
        overall_integrity_status IN ('VERIFIED', 'DISCREPANCIES_FOUND', 'MISLEADING_CLAIMS_DETECTED', 'NEEDS_REVIEW')
    ),
    findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    supported_count INT NOT NULL DEFAULT 0,
    partly_true_count INT NOT NULL DEFAULT 0,
    contradicted_count INT NOT NULL DEFAULT 0,
    not_in_policy_count INT NOT NULL DEFAULT 0,
    unclear_count INT NOT NULL DEFAULT 0,
    review_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_session_report_version UNIQUE (sales_session_id, report_version)
);

CREATE INDEX IF NOT EXISTS idx_verification_reports_session ON verification_reports (sales_session_id);
CREATE INDEX IF NOT EXISTS idx_verification_reports_customer ON verification_reports (customer_id);
CREATE INDEX IF NOT EXISTS idx_verification_reports_agent ON verification_reports (agent_id);
CREATE INDEX IF NOT EXISTS idx_verification_reports_policy_version ON verification_reports (policy_version_id);
CREATE INDEX IF NOT EXISTS idx_verification_reports_status ON verification_reports (status);
CREATE INDEX IF NOT EXISTS idx_verification_reports_created_at ON verification_reports (created_at DESC);

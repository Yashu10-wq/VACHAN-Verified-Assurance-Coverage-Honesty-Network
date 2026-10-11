-- ==============================================================================
-- InsureChain VoiceGuard — Migration 0003: Policy Catalogue & Registrations
-- ==============================================================================
-- Creates immutable versioned policy catalogues, exact numeric coverage limits,
-- agent-led customer registrations with consent, and customer confirmation lifecycle.

-- Master policy table
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insurer_name VARCHAR(255) NOT NULL,
    policy_name VARCHAR(255) NOT NULL,
    policy_code VARCHAR(64) NOT NULL UNIQUE,
    category VARCHAR(64) NOT NULL CHECK (category IN ('VEHICLE', 'HOSPITALIZATION', 'GENERIC')),
    description TEXT NOT NULL,
    coverage_limit NUMERIC(14, 2) NOT NULL CHECK (coverage_limit > 0),
    waiting_period_days INT NOT NULL DEFAULT 0 CHECK (waiting_period_days >= 0),
    claim_filing_window_days INT NOT NULL DEFAULT 30 CHECK (claim_filing_window_days > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_policies_code ON policies (policy_code);
CREATE INDEX IF NOT EXISTS idx_policies_category ON policies (category);

-- Versioned, immutable policy terms and private document metadata
CREATE TABLE IF NOT EXISTS policy_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    version_number INT NOT NULL CHECK (version_number > 0),
    document_storage_ref VARCHAR(255) NOT NULL,
    document_checksum VARCHAR(64) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE,
    terms_json JSONB DEFAULT '{}'::jsonb,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    published_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_policy_version UNIQUE (policy_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_policy_versions_published ON policy_versions (policy_id, is_published);

-- Policy registrations initiated by agents with explicit customer consent
CREATE TABLE IF NOT EXISTS policy_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    agent_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE RESTRICT,
    policy_version_id UUID NOT NULL REFERENCES policy_versions(id) ON DELETE RESTRICT,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING_VERIFICATION' CHECK (
        status IN (
            'PENDING_VERIFICATION',
            'PENDING_REVIEW',
            'AWAITING_CUSTOMER_CONFIRMATION',
            'CONFIRMED',
            'DECLINED',
            'CANCELLED'
        )
    ),
    customer_consent BOOLEAN NOT NULL DEFAULT FALSE,
    consent_timestamp TIMESTAMPTZ,
    consent_notes TEXT,
    customer_decision_at TIMESTAMPTZ,
    activated_at TIMESTAMPTZ,
    declined_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_registrations_customer ON policy_registrations (customer_id);
CREATE INDEX IF NOT EXISTS idx_registrations_agent ON policy_registrations (agent_id);
CREATE INDEX IF NOT EXISTS idx_registrations_status ON policy_registrations (status);

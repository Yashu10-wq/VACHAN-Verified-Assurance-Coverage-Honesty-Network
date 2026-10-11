-- ==============================================================================
-- InsureChain VoiceGuard — Migration 0005: Sales Sessions & STT Transcriptions
-- ==============================================================================
-- Relational schema for sales conversations, customer consent gating,
-- private Cloudinary audio references, and ElevenLabs Speech-to-Text records.

CREATE TABLE IF NOT EXISTS sales_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    agent_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    policy_id UUID REFERENCES policies(id) ON DELETE RESTRICT,
    policy_version_id UUID REFERENCES policy_versions(id) ON DELETE RESTRICT,
    registration_id UUID REFERENCES policy_registrations(id) ON DELETE SET NULL,
    audio_storage_ref VARCHAR(255) NOT NULL,
    audio_mime_type VARCHAR(64) NOT NULL,
    audio_file_size_bytes BIGINT NOT NULL CHECK (audio_file_size_bytes > 0),
    duration_seconds INT CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    audio_checksum VARCHAR(64) NOT NULL,
    customer_consent BOOLEAN NOT NULL DEFAULT FALSE,
    consent_timestamp TIMESTAMPTZ,
    consent_notes TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')
    ),
    transcript TEXT,
    detected_language VARCHAR(32),
    word_segments JSONB NOT NULL DEFAULT '[]'::jsonb,
    speaker_diarization JSONB NOT NULL DEFAULT '[]'::jsonb,
    provider_model VARCHAR(64) DEFAULT 'scribe_v2',
    error_category VARCHAR(64),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sales_sessions_customer ON sales_sessions (customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_sessions_agent ON sales_sessions (agent_id);
CREATE INDEX IF NOT EXISTS idx_sales_sessions_registration ON sales_sessions (registration_id);
CREATE INDEX IF NOT EXISTS idx_sales_sessions_status ON sales_sessions (status);
CREATE INDEX IF NOT EXISTS idx_sales_sessions_created_at ON sales_sessions (created_at DESC);

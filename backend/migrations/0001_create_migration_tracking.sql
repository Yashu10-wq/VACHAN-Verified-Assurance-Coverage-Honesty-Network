-- ==============================================================================
-- InsureChain VoiceGuard — Migration 0001: Schema Migration Tracking Table
-- ==============================================================================
-- Creates the internal migration audit table to track applied schema versions.
-- All future schema modifications must be versioned and recorded in this table.

CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations (version);

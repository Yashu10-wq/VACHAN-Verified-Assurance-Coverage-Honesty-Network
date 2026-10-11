-- ==============================================================================
-- InsureChain VoiceGuard — Migration 0002: Authentication, Identity & RBAC
-- ==============================================================================
-- Creates users, role constraints, account verification states, secure tokens,
-- refresh token revocation sessions, and durable security audit logs.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table supporting all three primary roles and explicit verification states
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    role VARCHAR(32) NOT NULL CHECK (role IN ('CUSTOMER', 'INSURANCE_AGENT', 'APPROVAL_AUTHORITY')),
    account_status VARCHAR(32) NOT NULL DEFAULT 'PENDING_VERIFICATION' CHECK (
        account_status IN ('PENDING_VERIFICATION', 'PENDING_APPROVAL', 'ACTIVE', 'REJECTED', 'SUSPENDED')
    ),
    email_verified_at TIMESTAMPTZ,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_account_status ON users (account_status);

-- Single-use hashed tokens for email verification, password reset, and customer activation
CREATE TABLE IF NOT EXISTS user_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_type VARCHAR(32) NOT NULL CHECK (
        token_type IN ('EMAIL_VERIFICATION', 'PASSWORD_RESET', 'CUSTOMER_ACTIVATION')
    ),
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_tokens_hash ON user_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_user_tokens_user_type ON user_tokens (user_id, token_type);

-- Refresh tokens for rotation and session revocation
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens (user_id);

-- Durable security audit log for security-sensitive identity events
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_role VARCHAR(32),
    action VARCHAR(64) NOT NULL,
    target_type VARCHAR(64) NOT NULL,
    target_id VARCHAR(64),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target ON audit_logs (target_type, target_id);

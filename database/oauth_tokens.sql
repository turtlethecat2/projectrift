-- Migration: Add oauth_tokens table for Outreach OAuth integration
-- Run: psql $DATABASE_URL -f database/oauth_tokens.sql

CREATE TABLE IF NOT EXISTS oauth_tokens (
    id             SERIAL PRIMARY KEY,
    provider       VARCHAR(50) NOT NULL UNIQUE DEFAULT 'outreach',
    access_token   TEXT NOT NULL,
    refresh_token  TEXT NOT NULL,
    expires_at     TIMESTAMPTZ NOT NULL,
    last_synced_at TIMESTAMPTZ,
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

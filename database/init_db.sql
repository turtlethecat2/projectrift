-- Project Rift Database Initialization Script
-- This script creates all necessary tables and seeds initial data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS event_log CASCADE;
DROP TABLE IF EXISTS raw_events CASCADE;
DROP TABLE IF EXISTS gamification_rules CASCADE;

-- Table: gamification_rules
-- Defines gold and XP values for each event type
CREATE TABLE gamification_rules (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) UNIQUE NOT NULL,
    gold_value INT NOT NULL DEFAULT 0,
    xp_value INT NOT NULL DEFAULT 0,
    display_name VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT positive_gold_rule CHECK (gold_value >= 0),
    CONSTRAINT positive_xp_rule CHECK (xp_value >= 0)
);

-- Table: raw_events
-- Stores all incoming webhook events
CREATE TABLE raw_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    gold_value INT NOT NULL,
    xp_value INT NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,

    CONSTRAINT valid_source CHECK (source IN ('outreach', 'nooks', 'manual', 'zapier')),
    CONSTRAINT positive_gold CHECK (gold_value >= 0),
    CONSTRAINT positive_xp CHECK (xp_value >= 0)
);

-- Table: event_log
-- Audit trail for all event operations
CREATE TABLE event_log (
    id SERIAL PRIMARY KEY,
    event_id UUID REFERENCES raw_events(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_events_date ON raw_events(created_at);
CREATE INDEX idx_events_type ON raw_events(event_type);
CREATE INDEX idx_events_source ON raw_events(source);
CREATE INDEX idx_events_processed ON raw_events(processed_at) WHERE processed_at IS NOT NULL;
CREATE INDEX idx_event_log_event_id ON event_log(event_id);
CREATE INDEX idx_event_log_created ON event_log(created_at);

-- Seed gamification rules
INSERT INTO gamification_rules (event_type, gold_value, xp_value, display_name, description) VALUES
('call_dial', 10, 5, 'Dial Attempt', 'Gold for making a call attempt'),
('call_connect', 25, 15, 'Call Connected', 'Bonus for reaching a prospect (no meeting)'),
('email_sent', 10, 3, 'Email Sent', 'Gold for sending a personalized email'),
('meeting_booked', 200, 100, 'Meeting Booked', 'Major achievement - meeting scheduled'),
('meeting_attended', 500, 200, 'Meeting Attended', 'Prospect showed up to meeting');

-- Create a function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for gamification_rules
CREATE TRIGGER update_gamification_rules_updated_at
    BEFORE UPDATE ON gamification_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Project Rift database initialized successfully!';
    RAISE NOTICE 'Tables created: gamification_rules, raw_events, event_log';
    RAISE NOTICE 'Seeded % gamification rules', (SELECT COUNT(*) FROM gamification_rules);
END $$;

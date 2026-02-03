-- =============================================================================
-- Axiom Design Engine - PostgreSQL Initialization Script
-- Runs on first container startup
-- =============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';

-- Grant privileges (if using different user)
-- GRANT ALL PRIVILEGES ON DATABASE axiom_engine TO axiom;

-- Create schema (optional, for organization)
-- CREATE SCHEMA IF NOT EXISTS axiom;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Axiom Design Engine database initialized at %', NOW();
END $$;

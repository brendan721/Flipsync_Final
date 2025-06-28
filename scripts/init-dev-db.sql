-- FlipSync Development Database Initialization
-- This script sets up the development databases for FlipSync

-- Create additional databases for FlipSync components
CREATE DATABASE IF NOT EXISTS flipsync_ai_tools;
CREATE DATABASE IF NOT EXISTS flipsync_test;

-- Create development user with appropriate permissions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'flipsync_dev') THEN
        CREATE ROLE flipsync_dev WITH LOGIN PASSWORD 'flipsync_dev_password';
    END IF;
END
$$;

-- Grant permissions to development user
GRANT ALL PRIVILEGES ON DATABASE flipsync TO flipsync_dev;
GRANT ALL PRIVILEGES ON DATABASE flipsync_ai_tools TO flipsync_dev;
GRANT ALL PRIVILEGES ON DATABASE flipsync_test TO flipsync_dev;

-- Connect to flipsync database and set up schema
\c flipsync;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "hstore";

-- Create basic schema for FlipSync
CREATE SCHEMA IF NOT EXISTS flipsync_core;
CREATE SCHEMA IF NOT EXISTS flipsync_auth;
CREATE SCHEMA IF NOT EXISTS flipsync_agents;

-- Grant schema permissions
GRANT ALL ON SCHEMA flipsync_core TO flipsync_dev;
GRANT ALL ON SCHEMA flipsync_auth TO flipsync_dev;
GRANT ALL ON SCHEMA flipsync_agents TO flipsync_dev;

-- Connect to AI tools database
\c flipsync_ai_tools;

-- Enable extensions for AI tools
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector" IF EXISTS;  -- For vector embeddings if available

-- Create AI tools schema
CREATE SCHEMA IF NOT EXISTS ai_tools;
CREATE SCHEMA IF NOT EXISTS knowledge_base;
CREATE SCHEMA IF NOT EXISTS agent_coordination;

-- Grant permissions
GRANT ALL ON SCHEMA ai_tools TO flipsync_dev;
GRANT ALL ON SCHEMA knowledge_base TO flipsync_dev;
GRANT ALL ON SCHEMA agent_coordination TO flipsync_dev;

-- Connect to test database
\c flipsync_test;

-- Enable extensions for testing
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create test schema
CREATE SCHEMA IF NOT EXISTS test_data;
GRANT ALL ON SCHEMA test_data TO flipsync_dev;

-- Return to default database
\c postgres;

-- Log completion
SELECT 'FlipSync development databases initialized successfully' AS status;

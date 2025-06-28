-- FlipSync Database Initialization Script
-- AGENT_CONTEXT: Creates separate databases for project data vs AI agent tooling
-- AGENT_PRIORITY: Enforces hard line between FlipSync app data and AI development tools
-- AGENT_PATTERN: Database separation for data integrity and security

-- Create FlipSync application database
CREATE DATABASE flipsync;

-- Create AI agent persistence database (separate from application data)
CREATE DATABASE ai_agent_persistence;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE flipsync TO postgres;
GRANT ALL PRIVILEGES ON DATABASE ai_agent_persistence TO postgres;

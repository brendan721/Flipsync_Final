-- FlipSync AI Tools Database Setup
-- This script creates a SEPARATE database for AI agent development tools
-- to maintain clear separation from FlipSync application data

-- Connect to PostgreSQL as postgres user
-- Usage: psql -h localhost -p 1432 -U postgres -f setup_ai_tools_database.sql

-- Create the AI tools database
CREATE DATABASE flipsync_ai_tools
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    TEMPLATE = template0;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE flipsync_ai_tools TO postgres;

-- Connect to the new database
\c flipsync_ai_tools;

-- Create AI agent persistence tables
CREATE TABLE IF NOT EXISTS agent_memory (
    id SERIAL PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    context_key VARCHAR(255) NOT NULL,
    context_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(agent_type, context_key)
);

CREATE TABLE IF NOT EXISTS code_insights (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(500),
    insight_type VARCHAR(100),
    insight_data JSONB,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_interactions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    interaction_type VARCHAR(50),
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_decision_trees (
    id SERIAL PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    decision_context VARCHAR(255),
    decision_data JSONB,
    outcome_success BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_learning_patterns (
    id SERIAL PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    pattern_type VARCHAR(100),
    pattern_data JSONB,
    success_rate FLOAT,
    usage_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_context_evolution (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    context_before JSONB,
    context_after JSONB,
    evolution_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_agent_memory_type_key ON agent_memory(agent_type, context_key);
CREATE INDEX idx_code_insights_file_path ON code_insights(file_path);
CREATE INDEX idx_agent_interactions_session ON agent_interactions(session_id);
CREATE INDEX idx_agent_decision_trees_type ON agent_decision_trees(agent_type);
CREATE INDEX idx_agent_learning_patterns_type ON agent_learning_patterns(agent_type);
CREATE INDEX idx_agent_context_evolution_session ON agent_context_evolution(session_id);

-- Create a view for recent agent activity
CREATE VIEW recent_agent_activity AS
SELECT 
    'memory' as activity_type,
    agent_type,
    context_key as activity_key,
    created_at
FROM agent_memory
WHERE created_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT 
    'interaction' as activity_type,
    'unknown' as agent_type,
    interaction_type as activity_key,
    created_at
FROM agent_interactions
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Insert initial test data
INSERT INTO agent_memory (agent_type, context_key, context_data) VALUES
('augment_code', 'initialization_test', '{"status": "database_setup_complete", "timestamp": "' || NOW() || '"}'),
('system', 'database_version', '{"version": "1.0", "created": "' || NOW() || '", "purpose": "AI agent development tools"}');

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_agent_memory_updated_at BEFORE UPDATE ON agent_memory FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_code_insights_updated_at BEFORE UPDATE ON code_insights FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agent_learning_patterns_updated_at BEFORE UPDATE ON agent_learning_patterns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions for future use
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Display setup completion message
SELECT 'FlipSync AI Tools Database Setup Complete!' as status,
       COUNT(*) as tables_created
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE';

-- Show the created tables
\dt

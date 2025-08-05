-- FlipSync Production Database Monitoring Configuration
-- This script sets up monitoring, logging, and performance tracking

-- Enable monitoring extensions
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_buffercache";

-- Create monitoring schema
CREATE SCHEMA IF NOT EXISTS monitoring AUTHORIZATION flipsync_app;

-- Database performance metrics table
CREATE TABLE IF NOT EXISTS monitoring.performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit VARCHAR(20),
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tags JSONB DEFAULT '{}'::jsonb
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_time 
ON monitoring.performance_metrics (metric_name, collected_at DESC);

-- Database connection monitoring
CREATE TABLE IF NOT EXISTS monitoring.connection_stats (
    id SERIAL PRIMARY KEY,
    total_connections INTEGER NOT NULL,
    active_connections INTEGER NOT NULL,
    idle_connections INTEGER NOT NULL,
    max_connections INTEGER NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Query performance tracking
CREATE TABLE IF NOT EXISTS monitoring.slow_queries (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    execution_time_ms NUMERIC NOT NULL,
    rows_examined INTEGER,
    rows_returned INTEGER,
    database_name VARCHAR(100),
    user_name VARCHAR(100),
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Backup monitoring
CREATE TABLE IF NOT EXISTS monitoring.backup_status (
    id SERIAL PRIMARY KEY,
    backup_name VARCHAR(200) NOT NULL,
    backup_type VARCHAR(50) NOT NULL, -- 'full', 'incremental', 'schema'
    status VARCHAR(20) NOT NULL, -- 'started', 'completed', 'failed'
    file_size_bytes BIGINT,
    duration_seconds INTEGER,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System health checks
CREATE TABLE IF NOT EXISTS monitoring.health_checks (
    id SERIAL PRIMARY KEY,
    check_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'healthy', 'warning', 'critical'
    message TEXT,
    response_time_ms NUMERIC,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create monitoring functions
CREATE OR REPLACE FUNCTION monitoring.collect_performance_metrics()
RETURNS void AS $$
BEGIN
    -- Collect database size metrics
    INSERT INTO monitoring.performance_metrics (metric_name, metric_value, metric_unit)
    SELECT 'database_size_mb', pg_database_size(current_database()) / 1024.0 / 1024.0, 'MB';
    
    -- Collect connection metrics
    INSERT INTO monitoring.connection_stats (
        total_connections, active_connections, idle_connections, max_connections
    )
    SELECT 
        (SELECT count(*) FROM pg_stat_activity),
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active'),
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle'),
        (SELECT setting::integer FROM pg_settings WHERE name = 'max_connections');
    
    -- Collect cache hit ratio
    INSERT INTO monitoring.performance_metrics (metric_name, metric_value, metric_unit)
    SELECT 
        'cache_hit_ratio',
        CASE 
            WHEN (blks_hit + blks_read) = 0 THEN 0
            ELSE (blks_hit::float / (blks_hit + blks_read)) * 100
        END,
        'percent'
    FROM pg_stat_database 
    WHERE datname = current_database();
    
    -- Collect transaction metrics
    INSERT INTO monitoring.performance_metrics (metric_name, metric_value, metric_unit)
    SELECT 'transactions_per_second', xact_commit + xact_rollback, 'tps'
    FROM pg_stat_database 
    WHERE datname = current_database();
    
    -- Collect deadlock count
    INSERT INTO monitoring.performance_metrics (metric_name, metric_value, metric_unit)
    SELECT 'deadlocks', deadlocks, 'count'
    FROM pg_stat_database 
    WHERE datname = current_database();
    
END;
$$ LANGUAGE plpgsql;

-- Function to identify slow queries
CREATE OR REPLACE FUNCTION monitoring.log_slow_queries(threshold_ms INTEGER DEFAULT 1000)
RETURNS void AS $$
BEGIN
    INSERT INTO monitoring.slow_queries (
        query_hash, query_text, execution_time_ms, 
        rows_examined, rows_returned, database_name, user_name
    )
    SELECT 
        md5(query),
        query,
        mean_exec_time,
        rows,
        calls,
        'flipsync_prod',
        'system'
    FROM pg_stat_statements 
    WHERE mean_exec_time > threshold_ms
    AND query NOT LIKE '%monitoring.%'
    AND query NOT LIKE '%pg_stat_%'
    ORDER BY mean_exec_time DESC
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;

-- Function to perform health checks
CREATE OR REPLACE FUNCTION monitoring.perform_health_checks()
RETURNS void AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    response_time NUMERIC;
BEGIN
    -- Database connectivity check
    start_time := clock_timestamp();
    PERFORM 1;
    end_time := clock_timestamp();
    response_time := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
    
    INSERT INTO monitoring.health_checks (check_name, status, message, response_time_ms)
    VALUES ('database_connectivity', 'healthy', 'Database is responding', response_time);
    
    -- Disk space check
    INSERT INTO monitoring.health_checks (check_name, status, message)
    SELECT 
        'disk_space',
        CASE 
            WHEN pg_database_size(current_database()) > 0.8 * 1024 * 1024 * 1024 * 1024 THEN 'warning'
            WHEN pg_database_size(current_database()) > 0.9 * 1024 * 1024 * 1024 * 1024 THEN 'critical'
            ELSE 'healthy'
        END,
        'Database size: ' || pg_size_pretty(pg_database_size(current_database()));
    
    -- Connection limit check
    INSERT INTO monitoring.health_checks (check_name, status, message)
    SELECT 
        'connection_limit',
        CASE 
            WHEN (SELECT count(*) FROM pg_stat_activity) > 0.8 * (SELECT setting::integer FROM pg_settings WHERE name = 'max_connections') THEN 'warning'
            WHEN (SELECT count(*) FROM pg_stat_activity) > 0.9 * (SELECT setting::integer FROM pg_settings WHERE name = 'max_connections') THEN 'critical'
            ELSE 'healthy'
        END,
        'Active connections: ' || (SELECT count(*) FROM pg_stat_activity) || '/' || (SELECT setting FROM pg_settings WHERE name = 'max_connections');
    
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old monitoring data
CREATE OR REPLACE FUNCTION monitoring.cleanup_old_data(retention_days INTEGER DEFAULT 30)
RETURNS void AS $$
BEGIN
    -- Clean up old performance metrics
    DELETE FROM monitoring.performance_metrics 
    WHERE collected_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    
    -- Clean up old connection stats
    DELETE FROM monitoring.connection_stats 
    WHERE collected_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    
    -- Clean up old slow queries
    DELETE FROM monitoring.slow_queries 
    WHERE executed_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    
    -- Clean up old health checks
    DELETE FROM monitoring.health_checks 
    WHERE checked_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    
    -- Clean up old backup status
    DELETE FROM monitoring.backup_status 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days;
    
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to monitoring functions
GRANT EXECUTE ON FUNCTION monitoring.collect_performance_metrics() TO flipsync_app;
GRANT EXECUTE ON FUNCTION monitoring.log_slow_queries(INTEGER) TO flipsync_app;
GRANT EXECUTE ON FUNCTION monitoring.perform_health_checks() TO flipsync_app;
GRANT EXECUTE ON FUNCTION monitoring.cleanup_old_data(INTEGER) TO flipsync_app;

-- Grant read access to monitoring tables for readonly user
GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO flipsync_readonly;

-- Create views for easy monitoring
CREATE OR REPLACE VIEW monitoring.current_performance AS
SELECT 
    metric_name,
    metric_value,
    metric_unit,
    collected_at
FROM monitoring.performance_metrics 
WHERE collected_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY collected_at DESC;

CREATE OR REPLACE VIEW monitoring.recent_health_status AS
SELECT DISTINCT ON (check_name)
    check_name,
    status,
    message,
    response_time_ms,
    checked_at
FROM monitoring.health_checks
ORDER BY check_name, checked_at DESC;

-- Grant access to views
GRANT SELECT ON monitoring.current_performance TO flipsync_readonly;
GRANT SELECT ON monitoring.recent_health_status TO flipsync_readonly;

-- Insert initial health check
SELECT monitoring.perform_health_checks();

-- Log monitoring setup completion
INSERT INTO monitoring.health_checks (check_name, status, message)
VALUES ('monitoring_setup', 'healthy', 'Database monitoring system initialized successfully');

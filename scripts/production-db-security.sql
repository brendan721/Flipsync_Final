-- FlipSync Production Database Security Configuration
-- This script implements security hardening for the production database

-- Enable security-related extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create security schema
CREATE SCHEMA IF NOT EXISTS security AUTHORIZATION flipsync_app;

-- Security configuration table
CREATE TABLE IF NOT EXISTS security.security_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert security configuration
INSERT INTO security.security_config (config_key, config_value, description) VALUES
('password_min_length', '12', 'Minimum password length requirement'),
('password_require_uppercase', 'true', 'Require uppercase letters in passwords'),
('password_require_lowercase', 'true', 'Require lowercase letters in passwords'),
('password_require_numbers', 'true', 'Require numbers in passwords'),
('password_require_symbols', 'true', 'Require symbols in passwords'),
('max_login_attempts', '5', 'Maximum failed login attempts before lockout'),
('lockout_duration_minutes', '30', 'Account lockout duration in minutes'),
('session_timeout_minutes', '30', 'Session timeout in minutes'),
('max_concurrent_sessions', '5', 'Maximum concurrent sessions per user'),
('password_history_count', '5', 'Number of previous passwords to remember'),
('force_password_change_days', '90', 'Force password change every N days'),
('enable_audit_logging', 'true', 'Enable comprehensive audit logging'),
('enable_encryption_at_rest', 'true', 'Enable encryption for sensitive data'),
('enable_ssl_only', 'true', 'Require SSL connections only'),
('enable_ip_whitelist', 'false', 'Enable IP address whitelisting'),
('enable_rate_limiting', 'true', 'Enable rate limiting for API endpoints')
ON CONFLICT (config_key) DO UPDATE SET 
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- Create password history table
CREATE TABLE IF NOT EXISTS security.password_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on password history
CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON security.password_history(user_id);
CREATE INDEX IF NOT EXISTS idx_password_history_created_at ON security.password_history(created_at);

-- Create login attempts table
CREATE TABLE IF NOT EXISTS security.login_attempts (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100),
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on login attempts
CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON security.login_attempts(email);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_address ON security.login_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempts_attempted_at ON security.login_attempts(attempted_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_success ON security.login_attempts(success);

-- Create IP whitelist table
CREATE TABLE IF NOT EXISTS security.ip_whitelist (
    id SERIAL PRIMARY KEY,
    ip_address CIDR NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on IP whitelist
CREATE INDEX IF NOT EXISTS idx_ip_whitelist_ip_address ON security.ip_whitelist(ip_address);
CREATE INDEX IF NOT EXISTS idx_ip_whitelist_is_active ON security.ip_whitelist(is_active);

-- Create rate limiting table
CREATE TABLE IF NOT EXISTS security.rate_limits (
    id BIGSERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL,  -- IP address, user ID, or API key
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP + INTERVAL '1 minute',
    is_blocked BOOLEAN DEFAULT false,
    blocked_until TIMESTAMP WITH TIME ZONE
);

-- Create indexes on rate limits
CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier ON security.rate_limits(identifier);
CREATE INDEX IF NOT EXISTS idx_rate_limits_endpoint ON security.rate_limits(endpoint);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window_end ON security.rate_limits(window_end);
CREATE INDEX IF NOT EXISTS idx_rate_limits_is_blocked ON security.rate_limits(is_blocked);

-- Create security events table
CREATE TABLE IF NOT EXISTS security.security_events (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'INFO',
    user_id UUID REFERENCES app.users(id),
    ip_address INET,
    user_agent TEXT,
    event_data JSONB,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on security events
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security.security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security.security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security.security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_ip_address ON security.security_events(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security.security_events(created_at);

-- Create function to log security events
CREATE OR REPLACE FUNCTION security.log_security_event(
    p_event_type VARCHAR(100),
    p_severity VARCHAR(20) DEFAULT 'INFO',
    p_user_id UUID DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_event_data JSONB DEFAULT NULL,
    p_description TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO security.security_events (
        event_type, severity, user_id, ip_address, user_agent, event_data, description
    ) VALUES (
        p_event_type, p_severity, p_user_id, p_ip_address, p_user_agent, p_event_data, p_description
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check password strength
CREATE OR REPLACE FUNCTION security.check_password_strength(password TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}';
    min_length INTEGER;
    require_uppercase BOOLEAN;
    require_lowercase BOOLEAN;
    require_numbers BOOLEAN;
    require_symbols BOOLEAN;
BEGIN
    -- Get security configuration
    SELECT config_value::INTEGER INTO min_length 
    FROM security.security_config WHERE config_key = 'password_min_length';
    
    SELECT config_value::BOOLEAN INTO require_uppercase 
    FROM security.security_config WHERE config_key = 'password_require_uppercase';
    
    SELECT config_value::BOOLEAN INTO require_lowercase 
    FROM security.security_config WHERE config_key = 'password_require_lowercase';
    
    SELECT config_value::BOOLEAN INTO require_numbers 
    FROM security.security_config WHERE config_key = 'password_require_numbers';
    
    SELECT config_value::BOOLEAN INTO require_symbols 
    FROM security.security_config WHERE config_key = 'password_require_symbols';
    
    -- Check password requirements
    result := jsonb_build_object(
        'valid', true,
        'errors', '[]'::jsonb
    );
    
    -- Check length
    IF LENGTH(password) < min_length THEN
        result := jsonb_set(result, '{valid}', 'false');
        result := jsonb_set(result, '{errors}', 
            result->'errors' || jsonb_build_array('Password must be at least ' || min_length || ' characters long'));
    END IF;
    
    -- Check uppercase
    IF require_uppercase AND password !~ '[A-Z]' THEN
        result := jsonb_set(result, '{valid}', 'false');
        result := jsonb_set(result, '{errors}', 
            result->'errors' || jsonb_build_array('Password must contain at least one uppercase letter'));
    END IF;
    
    -- Check lowercase
    IF require_lowercase AND password !~ '[a-z]' THEN
        result := jsonb_set(result, '{valid}', 'false');
        result := jsonb_set(result, '{errors}', 
            result->'errors' || jsonb_build_array('Password must contain at least one lowercase letter'));
    END IF;
    
    -- Check numbers
    IF require_numbers AND password !~ '[0-9]' THEN
        result := jsonb_set(result, '{valid}', 'false');
        result := jsonb_set(result, '{errors}', 
            result->'errors' || jsonb_build_array('Password must contain at least one number'));
    END IF;
    
    -- Check symbols
    IF require_symbols AND password !~ '[^A-Za-z0-9]' THEN
        result := jsonb_set(result, '{valid}', 'false');
        result := jsonb_set(result, '{errors}', 
            result->'errors' || jsonb_build_array('Password must contain at least one special character'));
    END IF;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check if IP is whitelisted
CREATE OR REPLACE FUNCTION security.is_ip_whitelisted(check_ip INET)
RETURNS BOOLEAN AS $$
DECLARE
    is_whitelisted BOOLEAN := false;
    whitelist_enabled BOOLEAN;
BEGIN
    -- Check if IP whitelisting is enabled
    SELECT config_value::BOOLEAN INTO whitelist_enabled 
    FROM security.security_config WHERE config_key = 'enable_ip_whitelist';
    
    -- If whitelisting is disabled, allow all IPs
    IF NOT whitelist_enabled THEN
        RETURN true;
    END IF;
    
    -- Check if IP is in whitelist
    SELECT EXISTS(
        SELECT 1 FROM security.ip_whitelist 
        WHERE is_active = true AND check_ip <<= ip_address
    ) INTO is_whitelisted;
    
    RETURN is_whitelisted;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to check rate limits
CREATE OR REPLACE FUNCTION security.check_rate_limit(
    p_identifier VARCHAR(255),
    p_endpoint VARCHAR(255),
    p_limit INTEGER DEFAULT 100,
    p_window_minutes INTEGER DEFAULT 1
) RETURNS JSONB AS $$
DECLARE
    current_count INTEGER := 0;
    window_start TIMESTAMP WITH TIME ZONE;
    window_end TIMESTAMP WITH TIME ZONE;
    is_blocked BOOLEAN := false;
    result JSONB;
BEGIN
    window_start := CURRENT_TIMESTAMP - (p_window_minutes || ' minutes')::INTERVAL;
    window_end := CURRENT_TIMESTAMP;
    
    -- Clean up old rate limit records
    DELETE FROM security.rate_limits 
    WHERE window_end < CURRENT_TIMESTAMP - INTERVAL '1 hour';
    
    -- Check current rate limit
    SELECT COALESCE(SUM(request_count), 0) INTO current_count
    FROM security.rate_limits
    WHERE identifier = p_identifier 
      AND endpoint = p_endpoint
      AND window_end > window_start;
    
    -- Check if currently blocked
    SELECT COALESCE(bool_or(is_blocked AND blocked_until > CURRENT_TIMESTAMP), false) INTO is_blocked
    FROM security.rate_limits
    WHERE identifier = p_identifier AND endpoint = p_endpoint;
    
    -- Update or insert rate limit record
    INSERT INTO security.rate_limits (identifier, endpoint, request_count, window_start, window_end)
    VALUES (p_identifier, p_endpoint, 1, window_start, window_end)
    ON CONFLICT (identifier, endpoint) DO UPDATE SET
        request_count = security.rate_limits.request_count + 1,
        window_end = CURRENT_TIMESTAMP;
    
    -- Check if limit exceeded
    IF current_count >= p_limit THEN
        is_blocked := true;
        UPDATE security.rate_limits 
        SET is_blocked = true, blocked_until = CURRENT_TIMESTAMP + INTERVAL '15 minutes'
        WHERE identifier = p_identifier AND endpoint = p_endpoint;
    END IF;
    
    result := jsonb_build_object(
        'allowed', NOT is_blocked,
        'current_count', current_count,
        'limit', p_limit,
        'window_minutes', p_window_minutes,
        'reset_time', window_end
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to encrypt sensitive data
CREATE OR REPLACE FUNCTION security.encrypt_sensitive_data(data TEXT, key_name TEXT DEFAULT 'default')
RETURNS TEXT AS $$
DECLARE
    encryption_key TEXT;
BEGIN
    -- In production, this should use a proper key management system
    -- For now, we'll use a simple approach
    encryption_key := 'CHANGE_ME_TO_SECURE_ENCRYPTION_KEY_32_CHARS';
    
    RETURN encode(pgp_sym_encrypt(data, encryption_key), 'base64');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to decrypt sensitive data
CREATE OR REPLACE FUNCTION security.decrypt_sensitive_data(encrypted_data TEXT, key_name TEXT DEFAULT 'default')
RETURNS TEXT AS $$
DECLARE
    encryption_key TEXT;
BEGIN
    -- In production, this should use a proper key management system
    encryption_key := 'CHANGE_ME_TO_SECURE_ENCRYPTION_KEY_32_CHARS';
    
    RETURN pgp_sym_decrypt(decode(encrypted_data, 'base64'), encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant permissions on security schema
GRANT USAGE ON SCHEMA security TO flipsync_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA security TO flipsync_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA security TO flipsync_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA security TO flipsync_app;

-- Grant read permissions to readonly user
GRANT USAGE ON SCHEMA security TO flipsync_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA security TO flipsync_readonly;

-- Set default permissions for future objects in security schema
ALTER DEFAULT PRIVILEGES IN SCHEMA security GRANT ALL ON TABLES TO flipsync_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA security GRANT ALL ON SEQUENCES TO flipsync_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA security GRANT EXECUTE ON FUNCTIONS TO flipsync_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA security GRANT SELECT ON TABLES TO flipsync_readonly;

-- Apply audit triggers to security tables
CREATE TRIGGER trigger_security_config_audit
    AFTER INSERT OR UPDATE OR DELETE ON security.security_config
    FOR EACH ROW
    EXECUTE FUNCTION audit.audit_trigger_function();

CREATE TRIGGER trigger_password_history_audit
    AFTER INSERT OR UPDATE OR DELETE ON security.password_history
    FOR EACH ROW
    EXECUTE FUNCTION audit.audit_trigger_function();

CREATE TRIGGER trigger_ip_whitelist_audit
    AFTER INSERT OR UPDATE OR DELETE ON security.ip_whitelist
    FOR EACH ROW
    EXECUTE FUNCTION audit.audit_trigger_function();

-- Log security initialization
SELECT security.log_security_event(
    'SECURITY_INIT',
    'INFO',
    NULL,
    NULL,
    NULL,
    '{"component": "database_security", "version": "1.0.0"}'::jsonb,
    'Database security configuration initialized'
);

-- FlipSync Production Database Initialization Script
-- This script sets up the production database with proper schema and initial data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create application database if it doesn't exist
-- Note: This runs after the main database is created by POSTGRES_DB

-- Create dedicated application user with limited privileges
DO $$
BEGIN
    -- Create application user if it doesn't exist
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'flipsync_app') THEN
        CREATE ROLE flipsync_app WITH LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;

    -- Create read-only user for monitoring/reporting
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'flipsync_readonly') THEN
        CREATE ROLE flipsync_readonly WITH LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;

    -- Create backup user
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'flipsync_backup') THEN
        CREATE ROLE flipsync_backup WITH LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;
END
$$;

-- Grant appropriate permissions (use current database name)
GRANT CONNECT ON DATABASE postgres TO flipsync_app;
GRANT CONNECT ON DATABASE postgres TO flipsync_readonly;
GRANT CONNECT ON DATABASE postgres TO flipsync_backup;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION flipsync_app;
CREATE SCHEMA IF NOT EXISTS audit AUTHORIZATION flipsync_app;
CREATE SCHEMA IF NOT EXISTS monitoring AUTHORIZATION flipsync_app;

-- Set default schema for application user
ALTER ROLE flipsync_app SET search_path = app, public;

-- Grant schema permissions
GRANT USAGE ON SCHEMA app TO flipsync_app;
GRANT CREATE ON SCHEMA app TO flipsync_app;
GRANT USAGE ON SCHEMA audit TO flipsync_app;
GRANT CREATE ON SCHEMA audit TO flipsync_app;
GRANT USAGE ON SCHEMA monitoring TO flipsync_app;
GRANT CREATE ON SCHEMA monitoring TO flipsync_app;

-- Grant read-only access to readonly user
GRANT USAGE ON SCHEMA app TO flipsync_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO flipsync_readonly;
GRANT USAGE ON SCHEMA audit TO flipsync_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO flipsync_readonly;
GRANT USAGE ON SCHEMA monitoring TO flipsync_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO flipsync_readonly;

-- Grant backup permissions
GRANT USAGE ON SCHEMA app TO flipsync_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO flipsync_backup;
GRANT USAGE ON SCHEMA audit TO flipsync_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO flipsync_backup;

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit.audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log (
            table_name, operation, new_data, changed_by, changed_at
        ) VALUES (
            TG_TABLE_NAME, TG_OP, row_to_json(NEW), current_user, now()
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log (
            table_name, operation, old_data, new_data, changed_by, changed_at
        ) VALUES (
            TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), current_user, now()
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log (
            table_name, operation, old_data, changed_by, changed_at
        ) VALUES (
            TG_TABLE_NAME, TG_OP, row_to_json(OLD), current_user, now()
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_by TEXT NOT NULL DEFAULT current_user,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create indexes on audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit.audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit.audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit.audit_log(changed_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_by ON audit.audit_log(changed_by);

-- Create inventory tables in app schema
CREATE TABLE IF NOT EXISTS app.inventory_items (
    id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    quantity INTEGER DEFAULT 0 CHECK (quantity >= 0),
    price DECIMAL(10,2) CHECK (price >= 0),
    cost DECIMAL(10,2) CHECK (cost >= 0),
    weight DECIMAL(10,3) CHECK (weight >= 0),
    dimensions VARCHAR(100),
    location VARCHAR(100),
    supplier VARCHAR(255),
    barcode VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    low_stock_threshold INTEGER DEFAULT 0 CHECK (low_stock_threshold >= 0),
    reorder_point INTEGER DEFAULT 0 CHECK (reorder_point >= 0),
    reorder_quantity INTEGER DEFAULT 0 CHECK (reorder_quantity >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Create performance indexes for inventory_items
CREATE INDEX IF NOT EXISTS idx_inventory_items_is_active ON app.inventory_items(is_active);
CREATE INDEX IF NOT EXISTS idx_inventory_items_category ON app.inventory_items(category);
CREATE INDEX IF NOT EXISTS idx_inventory_items_created_by ON app.inventory_items(created_by);
CREATE INDEX IF NOT EXISTS idx_inventory_items_created_at ON app.inventory_items(created_at);
CREATE INDEX IF NOT EXISTS idx_inventory_items_updated_at ON app.inventory_items(updated_at);
CREATE INDEX IF NOT EXISTS idx_inventory_items_quantity ON app.inventory_items(quantity);
CREATE INDEX IF NOT EXISTS idx_inventory_items_location ON app.inventory_items(location);
CREATE INDEX IF NOT EXISTS idx_inventory_items_supplier ON app.inventory_items(supplier);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_inventory_items_active_user ON app.inventory_items(is_active, created_by);
CREATE INDEX IF NOT EXISTS idx_inventory_items_active_category ON app.inventory_items(is_active, category);
CREATE INDEX IF NOT EXISTS idx_inventory_items_active_created ON app.inventory_items(is_active, created_at);
CREATE INDEX IF NOT EXISTS idx_inventory_items_low_stock ON app.inventory_items(is_active, quantity, low_stock_threshold);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_inventory_items_name_search ON app.inventory_items USING gin(to_tsvector('english', name)) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_inventory_items_description_search ON app.inventory_items USING gin(to_tsvector('english', description)) WHERE is_active = true AND description IS NOT NULL;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION app.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to inventory_items
CREATE TRIGGER trigger_inventory_items_updated_at
    BEFORE UPDATE ON app.inventory_items
    FOR EACH ROW
    EXECUTE FUNCTION app.update_updated_at_column();

-- Apply audit trigger to inventory_items
CREATE TRIGGER trigger_inventory_items_audit
    AFTER INSERT OR UPDATE OR DELETE ON app.inventory_items
    FOR EACH ROW
    EXECUTE FUNCTION audit.audit_trigger_function();

-- Create users table
CREATE TABLE IF NOT EXISTS app.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    status VARCHAR(20) DEFAULT 'active',
    is_verified BOOLEAN DEFAULT false,
    mfa_enabled BOOLEAN DEFAULT false,
    mfa_secret VARCHAR(255),
    last_login TIMESTAMP WITH TIME ZONE,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    preferences JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON app.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON app.users(username);
CREATE INDEX IF NOT EXISTS idx_users_status ON app.users(status);
CREATE INDEX IF NOT EXISTS idx_users_role ON app.users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON app.users(created_at);

-- Apply triggers to users table
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON app.users
    FOR EACH ROW
    EXECUTE FUNCTION app.update_updated_at_column();

CREATE TRIGGER trigger_users_audit
    AFTER INSERT OR UPDATE OR DELETE ON app.users
    FOR EACH ROW
    EXECUTE FUNCTION audit.audit_trigger_function();

-- Create sessions table for JWT token management
CREATE TABLE IF NOT EXISTS app.user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for sessions table
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON app.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token_jti ON app.user_sessions(token_jti);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON app.user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON app.user_sessions(expires_at);

-- Apply audit trigger to sessions table
CREATE TRIGGER trigger_user_sessions_audit
    AFTER INSERT OR UPDATE OR DELETE ON app.user_sessions
    FOR EACH ROW
    EXECUTE FUNCTION audit.audit_trigger_function();

-- Grant permissions on new tables to application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO flipsync_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA app TO flipsync_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO flipsync_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA audit TO flipsync_app;

-- Grant read permissions to readonly user on new tables
GRANT SELECT ON ALL TABLES IN SCHEMA app TO flipsync_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO flipsync_readonly;

-- Grant backup permissions on new tables
GRANT SELECT ON ALL TABLES IN SCHEMA app TO flipsync_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO flipsync_backup;

-- Set default permissions for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT ALL ON TABLES TO flipsync_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT ALL ON SEQUENCES TO flipsync_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON TABLES TO flipsync_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON TABLES TO flipsync_backup;

ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON TABLES TO flipsync_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON SEQUENCES TO flipsync_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT SELECT ON TABLES TO flipsync_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT SELECT ON TABLES TO flipsync_backup;

-- Create initial admin user (password should be changed immediately)
INSERT INTO app.users (email, username, password_hash, first_name, last_name, role, is_verified)
VALUES (
    'admin@flipsync.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.',  -- 'admin123' - CHANGE IMMEDIATELY
    'System',
    'Administrator',
    'admin',
    true
) ON CONFLICT (email) DO NOTHING;

-- Log initialization completion
INSERT INTO audit.audit_log (table_name, operation, new_data, changed_by)
VALUES ('database', 'INITIALIZE', '{"status": "completed", "version": "1.0.0"}', 'system');

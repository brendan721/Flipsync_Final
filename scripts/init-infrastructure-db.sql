-- FlipSync Infrastructure Database Initialization
-- This script sets up the shared database infrastructure

-- Create users first (PostgreSQL syntax)
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'flipsync_user') THEN
      CREATE USER flipsync_user WITH PASSWORD 'flipsync_secure_password';
   END IF;
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'flipsync_ai_user') THEN
      CREATE USER flipsync_ai_user WITH PASSWORD 'flipsync_ai_secure_password';
   END IF;
END
$do$;

-- Create databases for different projects (simple approach)
-- Note: These will fail if databases exist, but that's okay
CREATE DATABASE flipsync_dev;
CREATE DATABASE flipsync_test;
CREATE DATABASE flipsync_prod;
CREATE DATABASE flipsync_ai_tools;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE flipsync_dev TO flipsync_user;
GRANT ALL PRIVILEGES ON DATABASE flipsync_test TO flipsync_user;
GRANT ALL PRIVILEGES ON DATABASE flipsync_prod TO flipsync_user;
GRANT ALL PRIVILEGES ON DATABASE flipsync_ai_tools TO flipsync_ai_user;

-- Grant permissions to postgres user for administrative tasks
GRANT ALL PRIVILEGES ON DATABASE flipsync_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE flipsync_test TO postgres;
GRANT ALL PRIVILEGES ON DATABASE flipsync_prod TO postgres;
GRANT ALL PRIVILEGES ON DATABASE flipsync_ai_tools TO postgres;

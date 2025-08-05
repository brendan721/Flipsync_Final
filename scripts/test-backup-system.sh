#!/bin/bash

# FlipSync Database Backup System Test
# This script tests the backup and restore functionality

set -euo pipefail

# Configuration
TEST_DIR="/tmp/flipsync_backup_test"
BACKUP_DIR="/var/backups/postgresql"
TEST_DB="flipsync_backup_test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

success() {
    log "${GREEN}✅ $1${NC}"
}

warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

error() {
    log "${RED}❌ $1${NC}"
}

# Test database connection
test_database_connection() {
    log "Testing database connection..."
    
    if pg_isready -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" &> /dev/null; then
        success "Database connection successful"
        return 0
    else
        error "Database connection failed"
        return 1
    fi
}

# Create test database and data
create_test_database() {
    log "Creating test database and sample data..."
    
    # Create test database
    createdb -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" "$TEST_DB" 2>/dev/null || true
    
    # Create test table and insert sample data
    psql -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" -d "$TEST_DB" << EOF
CREATE TABLE IF NOT EXISTS test_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    value INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO test_data (name, value) VALUES 
('test_record_1', 100),
('test_record_2', 200),
('test_record_3', 300);
EOF
    
    success "Test database created with sample data"
}

# Test backup creation
test_backup_creation() {
    log "Testing backup creation..."
    
    # Set environment variables for backup script
    export PGDATABASE="$TEST_DB"
    export BACKUP_RETENTION_DAYS=1
    export BACKUP_ENCRYPTION_KEY="test_encryption_key_123"
    
    # Run backup script
    if ./scripts/backup-postgres.sh; then
        success "Backup creation successful"
        
        # Check if backup files were created
        local backup_count=$(find "$BACKUP_DIR" -name "*backup_*" -type f | wc -l)
        if [ "$backup_count" -gt 0 ]; then
            success "Backup files found: $backup_count files"
        else
            error "No backup files found"
            return 1
        fi
    else
        error "Backup creation failed"
        return 1
    fi
}

# Test backup verification
test_backup_verification() {
    log "Testing backup verification..."
    
    # Find the most recent backup
    local latest_backup=$(find "$BACKUP_DIR" -name "*backup_*.sql.gz.enc" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -n "$latest_backup" ] && [ -f "$latest_backup" ]; then
        success "Latest backup found: $(basename "$latest_backup")"
        
        # Check if checksum file exists
        if [ -f "${latest_backup}.sha256" ]; then
            success "Checksum file found"
            
            # Verify checksum
            if (cd "$(dirname "$latest_backup")" && sha256sum -c "$(basename "${latest_backup}.sha256")" &> /dev/null); then
                success "Backup integrity verified"
            else
                error "Backup integrity check failed"
                return 1
            fi
        else
            warning "Checksum file not found"
        fi
    else
        error "No backup files found for verification"
        return 1
    fi
}

# Test backup restore
test_backup_restore() {
    log "Testing backup restore..."
    
    # Find the most recent backup
    local latest_backup=$(find "$BACKUP_DIR" -name "*backup_*.sql.gz.enc" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -n "$latest_backup" ] && [ -f "$latest_backup" ]; then
        # Create restore test database
        local restore_db="${TEST_DB}_restore"
        dropdb -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" "$restore_db" 2>/dev/null || true
        
        # Set environment variables for restore script
        export BACKUP_ENCRYPTION_KEY="test_encryption_key_123"
        
        # Run restore script
        if ./scripts/restore-postgres.sh --force --target-db "$restore_db" "$(basename "$latest_backup")"; then
            success "Backup restore successful"
            
            # Verify restored data
            local record_count=$(psql -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" -d "$restore_db" -t -c "SELECT COUNT(*) FROM test_data;" | xargs)
            
            if [ "$record_count" = "3" ]; then
                success "Restored data verified: $record_count records found"
            else
                error "Data verification failed: expected 3 records, found $record_count"
                return 1
            fi
            
            # Clean up restore test database
            dropdb -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" "$restore_db" 2>/dev/null || true
        else
            error "Backup restore failed"
            return 1
        fi
    else
        error "No backup files found for restore test"
        return 1
    fi
}

# Test backup cleanup
test_backup_cleanup() {
    log "Testing backup cleanup..."
    
    # Create old test backup files
    local old_backup="${BACKUP_DIR}/flipsync_backup_old_test.sql.gz"
    touch "$old_backup"
    touch "${old_backup}.sha256"
    touch "${old_backup%.sql.gz}.metadata"
    
    # Set file modification time to 31 days ago
    find "$BACKUP_DIR" -name "*old_test*" -exec touch -d "31 days ago" {} \;
    
    # Run backup script with cleanup
    export PGDATABASE="$TEST_DB"
    export BACKUP_RETENTION_DAYS=30
    
    if ./scripts/backup-postgres.sh; then
        # Check if old files were cleaned up
        if [ ! -f "$old_backup" ]; then
            success "Old backup files cleaned up successfully"
        else
            warning "Old backup files still exist"
        fi
    else
        error "Backup cleanup test failed"
        return 1
    fi
}

# Cleanup test environment
cleanup_test_environment() {
    log "Cleaning up test environment..."
    
    # Drop test database
    dropdb -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" "$TEST_DB" 2>/dev/null || true
    
    # Remove test backup files
    find "$BACKUP_DIR" -name "*test*" -type f -delete 2>/dev/null || true
    
    # Remove test directory
    rm -rf "$TEST_DIR" 2>/dev/null || true
    
    success "Test environment cleaned up"
}

# Main test execution
main() {
    log "🔧 Starting FlipSync Database Backup System Test"
    log "=" * 60
    
    # Create test directory
    mkdir -p "$TEST_DIR"
    mkdir -p "$BACKUP_DIR"
    
    local tests_passed=0
    local tests_failed=0
    
    # Run tests
    if test_database_connection; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    if create_test_database; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    if test_backup_creation; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    if test_backup_verification; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    if test_backup_restore; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    if test_backup_cleanup; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    # Cleanup
    cleanup_test_environment
    
    # Report results
    log "=" * 60
    log "🔧 FlipSync Database Backup System Test Results"
    log "=" * 60
    success "Tests Passed: $tests_passed"
    if [ $tests_failed -gt 0 ]; then
        error "Tests Failed: $tests_failed"
    else
        log "Tests Failed: $tests_failed"
    fi
    
    if [ $tests_failed -eq 0 ]; then
        success "🎉 All backup system tests passed!"
        return 0
    else
        error "❌ Some backup system tests failed"
        return 1
    fi
}

# Handle script termination
trap 'cleanup_test_environment' INT TERM EXIT

# Run main function
main "$@"

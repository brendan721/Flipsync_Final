#!/bin/bash

# FlipSync PostgreSQL Backup Script
# This script creates encrypted backups of the PostgreSQL database

set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/postgresql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="flipsync_backup_${TIMESTAMP}"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
ENCRYPTION_KEY=${BACKUP_ENCRYPTION_KEY:-""}

# Database connection settings
DB_HOST=${PGHOST:-"postgres-production"}
DB_PORT=${PGPORT:-5432}
DB_NAME=${PGDATABASE:-"flipsync_prod"}
DB_USER=${PGUSER:-"flipsync_backup"}

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${BACKUP_DIR}/backup.log"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if backup directory exists
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory"
    fi
    
    # Check if pg_dump is available
    if ! command -v pg_dump &> /dev/null; then
        error_exit "pg_dump not found"
    fi
    
    # Check if openssl is available for encryption
    if [ -n "$ENCRYPTION_KEY" ] && ! command -v openssl &> /dev/null; then
        error_exit "openssl not found but encryption is enabled"
    fi
    
    # Test database connection
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" &> /dev/null; then
        error_exit "Cannot connect to database"
    fi
    
    log "Prerequisites check passed"
}

# Create database backup
create_backup() {
    log "Starting database backup..."
    
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.sql"
    local compressed_file="${backup_file}.gz"
    local encrypted_file="${compressed_file}.enc"
    
    # Create SQL dump
    log "Creating SQL dump..."
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        --no-privileges \
        --no-owner \
        --file="$backup_file" || error_exit "Failed to create SQL dump"
    
    # Compress the backup
    log "Compressing backup..."
    gzip "$backup_file" || error_exit "Failed to compress backup"
    
    # Encrypt if encryption key is provided
    if [ -n "$ENCRYPTION_KEY" ]; then
        log "Encrypting backup..."
        openssl enc -aes-256-cbc -salt -in "$compressed_file" -out "$encrypted_file" -k "$ENCRYPTION_KEY" || error_exit "Failed to encrypt backup"
        rm "$compressed_file"
        backup_file="$encrypted_file"
    else
        backup_file="$compressed_file"
    fi
    
    # Calculate checksum
    local checksum=$(sha256sum "$backup_file" | cut -d' ' -f1)
    echo "$checksum" > "${backup_file}.sha256"
    
    # Get file size
    local file_size=$(du -h "$backup_file" | cut -f1)
    
    log "Backup completed successfully"
    log "File: $backup_file"
    log "Size: $file_size"
    log "Checksum: $checksum"
    
    # Create backup metadata
    cat > "${BACKUP_DIR}/${BACKUP_NAME}.metadata" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "database": "$DB_NAME",
    "host": "$DB_HOST",
    "port": $DB_PORT,
    "user": "$DB_USER",
    "file_path": "$backup_file",
    "file_size": "$file_size",
    "checksum": "$checksum",
    "encrypted": $([ -n "$ENCRYPTION_KEY" ] && echo "true" || echo "false"),
    "compression": "gzip",
    "format": "custom",
    "created_at": "$(date -Iseconds)"
}
EOF
}

# Create schema-only backup
create_schema_backup() {
    log "Creating schema-only backup..."
    
    local schema_file="${BACKUP_DIR}/${BACKUP_NAME}_schema.sql"
    
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose \
        --no-password \
        --schema-only \
        --file="$schema_file" || error_exit "Failed to create schema backup"
    
    gzip "$schema_file"
    log "Schema backup completed: ${schema_file}.gz"
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
    
    find "$BACKUP_DIR" -name "flipsync_backup_*" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.metadata" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.sha256" -type f -mtime +$RETENTION_DAYS -delete
    
    log "Cleanup completed"
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    local checksum_file="${backup_file}.sha256"
    
    if [ -f "$checksum_file" ]; then
        log "Verifying backup integrity..."
        if sha256sum -c "$checksum_file" &> /dev/null; then
            log "Backup integrity verified"
        else
            error_exit "Backup integrity check failed"
        fi
    fi
}

# Send backup notification (placeholder for monitoring integration)
send_notification() {
    local status="$1"
    local message="$2"
    
    # This is a placeholder for integration with monitoring systems
    # In production, this could send notifications to Slack, email, etc.
    log "NOTIFICATION [$status]: $message"
    
    # Example: Send to webhook
    # curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" \
    #      -d "{\"status\": \"$status\", \"message\": \"$message\", \"timestamp\": \"$(date -Iseconds)\"}"
}

# Main execution
main() {
    log "Starting FlipSync database backup process"
    
    # Check prerequisites
    check_prerequisites
    
    # Create backups
    create_backup
    create_schema_backup
    
    # Verify backup
    local backup_file="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"
    if [ -n "$ENCRYPTION_KEY" ]; then
        backup_file="${backup_file}.enc"
    fi
    verify_backup "$backup_file"
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Send success notification
    send_notification "SUCCESS" "Database backup completed successfully: $BACKUP_NAME"
    
    log "Backup process completed successfully"
}

# Handle script termination
trap 'error_exit "Backup process interrupted"' INT TERM

# Run main function
main "$@"

#!/bin/bash

# FlipSync PostgreSQL Restore Script
# This script restores encrypted backups of the PostgreSQL database

set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/postgresql"
ENCRYPTION_KEY=${BACKUP_ENCRYPTION_KEY:-""}

# Database connection settings
DB_HOST=${PGHOST:-"postgres-production"}
DB_PORT=${PGPORT:-5432}
DB_NAME=${PGDATABASE:-"flipsync_prod"}
DB_USER=${PGUSER:-"flipsync_user"}

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${BACKUP_DIR}/restore.log"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS] BACKUP_FILE

Restore FlipSync PostgreSQL database from backup

OPTIONS:
    -h, --help              Show this help message
    -f, --force             Force restore without confirmation
    -s, --schema-only       Restore schema only
    -d, --data-only         Restore data only
    -t, --target-db NAME    Target database name (default: $DB_NAME)
    -v, --verify            Verify backup before restore

EXAMPLES:
    $0 flipsync_backup_20231201_120000.sql.gz.enc
    $0 --schema-only --target-db test_db backup.sql.gz
    $0 --verify --force latest_backup.sql.gz.enc

EOF
}

# Parse command line arguments
parse_arguments() {
    FORCE=false
    SCHEMA_ONLY=false
    DATA_ONLY=false
    VERIFY=false
    TARGET_DB="$DB_NAME"
    BACKUP_FILE=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -s|--schema-only)
                SCHEMA_ONLY=true
                shift
                ;;
            -d|--data-only)
                DATA_ONLY=true
                shift
                ;;
            -t|--target-db)
                TARGET_DB="$2"
                shift 2
                ;;
            -v|--verify)
                VERIFY=true
                shift
                ;;
            -*)
                error_exit "Unknown option: $1"
                ;;
            *)
                if [ -z "$BACKUP_FILE" ]; then
                    BACKUP_FILE="$1"
                else
                    error_exit "Multiple backup files specified"
                fi
                shift
                ;;
        esac
    done

    if [ -z "$BACKUP_FILE" ]; then
        error_exit "No backup file specified. Use --help for usage information."
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if pg_restore is available
    if ! command -v pg_restore &> /dev/null; then
        error_exit "pg_restore not found"
    fi
    
    # Check if openssl is available for decryption
    if [[ "$BACKUP_FILE" == *.enc ]] && ! command -v openssl &> /dev/null; then
        error_exit "openssl not found but backup is encrypted"
    fi
    
    # Test database connection
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres &> /dev/null; then
        error_exit "Cannot connect to database server"
    fi
    
    log "Prerequisites check passed"
}

# Find backup file
find_backup_file() {
    local file="$1"
    
    # If absolute path, use as-is
    if [[ "$file" == /* ]]; then
        BACKUP_PATH="$file"
    # If relative path, look in backup directory
    elif [ -f "$BACKUP_DIR/$file" ]; then
        BACKUP_PATH="$BACKUP_DIR/$file"
    # If just filename, look for it
    elif [ -f "$file" ]; then
        BACKUP_PATH="$file"
    else
        error_exit "Backup file not found: $file"
    fi
    
    if [ ! -f "$BACKUP_PATH" ]; then
        error_exit "Backup file does not exist: $BACKUP_PATH"
    fi
    
    log "Found backup file: $BACKUP_PATH"
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
    else
        log "Warning: No checksum file found, skipping integrity check"
    fi
}

# Prepare backup file for restore
prepare_backup() {
    local source_file="$1"
    TEMP_DIR=$(mktemp -d)
    RESTORE_FILE="$source_file"
    
    # Decrypt if encrypted
    if [[ "$source_file" == *.enc ]]; then
        if [ -z "$ENCRYPTION_KEY" ]; then
            error_exit "Backup is encrypted but no encryption key provided"
        fi
        
        log "Decrypting backup..."
        local decrypted_file="${TEMP_DIR}/$(basename "${source_file%.enc}")"
        openssl enc -aes-256-cbc -d -in "$source_file" -out "$decrypted_file" -k "$ENCRYPTION_KEY" || error_exit "Failed to decrypt backup"
        RESTORE_FILE="$decrypted_file"
    fi
    
    # Decompress if compressed
    if [[ "$RESTORE_FILE" == *.gz ]]; then
        log "Decompressing backup..."
        local decompressed_file="${TEMP_DIR}/$(basename "${RESTORE_FILE%.gz}")"
        gunzip -c "$RESTORE_FILE" > "$decompressed_file" || error_exit "Failed to decompress backup"
        RESTORE_FILE="$decompressed_file"
    fi
    
    log "Backup prepared for restore: $RESTORE_FILE"
}

# Create target database if it doesn't exist
create_target_database() {
    log "Checking target database: $TARGET_DB"
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -lqt | cut -d \| -f 1 | grep -qw "$TARGET_DB"; then
        log "Target database exists: $TARGET_DB"
        
        if [ "$FORCE" = false ]; then
            read -p "Database $TARGET_DB exists. Continue with restore? [y/N]: " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log "Restore cancelled by user"
                exit 0
            fi
        fi
    else
        log "Creating target database: $TARGET_DB"
        createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TARGET_DB" || error_exit "Failed to create database"
    fi
}

# Perform database restore
perform_restore() {
    log "Starting database restore..."
    
    local restore_options=(
        -h "$DB_HOST"
        -p "$DB_PORT"
        -U "$DB_USER"
        -d "$TARGET_DB"
        --verbose
        --no-password
    )
    
    # Add specific restore options
    if [ "$SCHEMA_ONLY" = true ]; then
        restore_options+=(--schema-only)
        log "Restoring schema only"
    elif [ "$DATA_ONLY" = true ]; then
        restore_options+=(--data-only)
        log "Restoring data only"
    else
        log "Restoring full database"
    fi
    
    # Perform restore
    pg_restore "${restore_options[@]}" "$RESTORE_FILE" || error_exit "Failed to restore database"
    
    log "Database restore completed successfully"
}

# Cleanup temporary files
cleanup() {
    if [ -n "${TEMP_DIR:-}" ] && [ -d "$TEMP_DIR" ]; then
        log "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# Send restore notification
send_notification() {
    local status="$1"
    local message="$2"
    
    log "NOTIFICATION [$status]: $message"
    
    # Example: Send to webhook
    # curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" \
    #      -d "{\"status\": \"$status\", \"message\": \"$message\", \"timestamp\": \"$(date -Iseconds)\"}"
}

# Main execution
main() {
    log "Starting FlipSync database restore process"
    
    # Parse arguments
    parse_arguments "$@"
    
    # Check prerequisites
    check_prerequisites
    
    # Find backup file
    find_backup_file "$BACKUP_FILE"
    
    # Verify backup if requested
    if [ "$VERIFY" = true ]; then
        verify_backup "$BACKUP_PATH"
    fi
    
    # Prepare backup for restore
    prepare_backup "$BACKUP_PATH"
    
    # Create target database
    create_target_database
    
    # Perform restore
    perform_restore
    
    # Send success notification
    send_notification "SUCCESS" "Database restore completed successfully to $TARGET_DB"
    
    log "Restore process completed successfully"
}

# Handle script termination
trap 'cleanup; error_exit "Restore process interrupted"' INT TERM EXIT

# Run main function
main "$@"

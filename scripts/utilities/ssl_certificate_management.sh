#!/bin/bash

# FlipSync SSL Certificate Management Script
# ==========================================
# Comprehensive SSL certificate monitoring and management for production

set -e

# Configuration
DOMAIN="flipsyncai.com"
WWW_DOMAIN="www.flipsyncai.com"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
NGINX_CONFIG="/etc/nginx/sites-available/flipsyncai.com"
LOG_FILE="/var/log/flipsync/ssl_monitoring.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    local message="$1"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[$timestamp]${NC} $message"
    echo "[$timestamp] $message" >> "$LOG_FILE" 2>/dev/null || true
}

error() {
    local message="$1"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[ERROR $timestamp]${NC} $message"
    echo "[ERROR $timestamp] $message" >> "$LOG_FILE" 2>/dev/null || true
}

success() {
    local message="$1"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[SUCCESS $timestamp]${NC} $message"
    echo "[SUCCESS $timestamp] $message" >> "$LOG_FILE" 2>/dev/null || true
}

warning() {
    local message="$1"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[WARNING $timestamp]${NC} $message"
    echo "[WARNING $timestamp] $message" >> "$LOG_FILE" 2>/dev/null || true
}

# Function to check if running on production server
check_production_server() {
    if [[ "$(hostname)" != *"flipsync"* ]] && [[ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
        error "This script must be run on the production server (192.168.110.71)"
        exit 1
    fi
}

# Function to create log directory
setup_logging() {
    mkdir -p /var/log/flipsync
    touch "$LOG_FILE"
}

# Function to check certificate status
check_certificate_status() {
    log "Checking SSL certificate status..."
    
    if [[ ! -f "$CERT_PATH/fullchain.pem" ]]; then
        error "SSL certificate not found at $CERT_PATH/fullchain.pem"
        return 1
    fi
    
    # Get certificate expiry date
    local expiry_date=$(openssl x509 -enddate -noout -in "$CERT_PATH/fullchain.pem" | cut -d= -f2)
    local expiry_timestamp=$(date -d "$expiry_date" +%s)
    local current_timestamp=$(date +%s)
    local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
    
    log "Certificate expiry date: $expiry_date"
    log "Days until expiry: $days_until_expiry"
    
    if [[ $days_until_expiry -lt 30 ]]; then
        warning "Certificate expires in $days_until_expiry days - renewal recommended"
    elif [[ $days_until_expiry -lt 7 ]]; then
        error "Certificate expires in $days_until_expiry days - URGENT renewal required"
        return 1
    else
        success "Certificate is valid for $days_until_expiry days"
    fi
    
    # Check certificate domains
    local cert_domains=$(openssl x509 -text -noout -in "$CERT_PATH/fullchain.pem" | grep -A1 "Subject Alternative Name" | tail -1 | sed 's/DNS://g' | tr ',' '\n' | tr -d ' ')
    
    log "Certificate covers domains:"
    echo "$cert_domains" | while read domain; do
        if [[ -n "$domain" ]]; then
            log "  - $domain"
        fi
    done
    
    return 0
}

# Function to verify nginx SSL configuration
verify_nginx_ssl_config() {
    log "Verifying nginx SSL configuration..."
    
    if [[ ! -f "$NGINX_CONFIG" ]]; then
        error "Nginx configuration not found at $NGINX_CONFIG"
        return 1
    fi
    
    # Check SSL certificate paths in nginx config
    local ssl_cert_line=$(grep "ssl_certificate " "$NGINX_CONFIG" | head -1)
    local ssl_key_line=$(grep "ssl_certificate_key " "$NGINX_CONFIG" | head -1)
    
    if echo "$ssl_cert_line" | grep -q "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"; then
        success "Nginx SSL certificate path is correct"
    else
        error "Nginx SSL certificate path is incorrect: $ssl_cert_line"
        return 1
    fi
    
    if echo "$ssl_key_line" | grep -q "/etc/letsencrypt/live/$DOMAIN/privkey.pem"; then
        success "Nginx SSL private key path is correct"
    else
        error "Nginx SSL private key path is incorrect: $ssl_key_line"
        return 1
    fi
    
    # Test nginx configuration
    if nginx -t 2>/dev/null; then
        success "Nginx configuration test passed"
    else
        error "Nginx configuration test failed"
        return 1
    fi
    
    return 0
}

# Function to check certbot timer status
check_certbot_timer() {
    log "Checking certbot automatic renewal status..."
    
    if systemctl is-active --quiet certbot.timer; then
        success "Certbot timer is active"
        
        # Get next run time
        local next_run=$(systemctl list-timers certbot.timer --no-pager | grep certbot.timer | awk '{print $1, $2, $3}')
        log "Next automatic renewal: $next_run"
    else
        error "Certbot timer is not active"
        return 1
    fi
    
    # Check certbot service status
    if systemctl list-unit-files | grep -q "certbot.service"; then
        success "Certbot service is available"
    else
        error "Certbot service is not available"
        return 1
    fi
    
    return 0
}

# Function to test certificate renewal (dry run)
test_certificate_renewal() {
    log "Testing certificate renewal (dry run)..."
    
    local renewal_output=$(certbot renew --dry-run 2>&1)
    local renewal_status=$?
    
    if [[ $renewal_status -eq 0 ]]; then
        success "Certificate renewal test passed"
        log "Renewal test output: $renewal_output"
    else
        error "Certificate renewal test failed"
        error "Renewal test output: $renewal_output"
        return 1
    fi
    
    return 0
}

# Function to validate SSL connection
validate_ssl_connection() {
    log "Validating SSL connections..."
    
    # Test main domain
    local ssl_check_main=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    if [[ -n "$ssl_check_main" ]]; then
        success "SSL connection to $DOMAIN is working"
    else
        error "SSL connection to $DOMAIN failed"
        return 1
    fi
    
    # Test www domain
    local ssl_check_www=$(echo | openssl s_client -servername "$WWW_DOMAIN" -connect "$WWW_DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    if [[ -n "$ssl_check_www" ]]; then
        success "SSL connection to $WWW_DOMAIN is working"
    else
        error "SSL connection to $WWW_DOMAIN failed"
        return 1
    fi
    
    return 0
}

# Function to check SSL security configuration
check_ssl_security() {
    log "Checking SSL security configuration..."
    
    # Test SSL protocols
    local ssl_protocols=$(nmap --script ssl-enum-ciphers -p 443 "$DOMAIN" 2>/dev/null | grep "TLSv" || echo "Could not determine SSL protocols")
    log "SSL protocols: $ssl_protocols"
    
    # Check for weak ciphers (basic check)
    if grep -q "ssl_protocols.*TLSv1\.2.*TLSv1\.3" "$NGINX_CONFIG"; then
        success "Strong SSL protocols configured (TLS 1.2 and 1.3)"
    else
        warning "SSL protocol configuration should be reviewed"
    fi
    
    # Check HSTS header
    local hsts_header=$(curl -s -I "https://$WWW_DOMAIN" 2>/dev/null | grep -i "strict-transport-security" || echo "")
    if [[ -n "$hsts_header" ]]; then
        success "HSTS header is configured: $hsts_header"
    else
        warning "HSTS header not found"
    fi
    
    return 0
}

# Function to create monitoring cron job
setup_monitoring_cron() {
    log "Setting up SSL monitoring cron job..."
    
    local cron_job="0 6 * * * /opt/flipsync/ssl_certificate_management.sh monitor >> /var/log/flipsync/ssl_cron.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "ssl_certificate_management.sh"; then
        log "SSL monitoring cron job already exists"
    else
        # Add cron job
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        success "SSL monitoring cron job added (daily at 6 AM)"
    fi
}

# Function to run comprehensive monitoring
run_monitoring() {
    log "Running comprehensive SSL monitoring..."
    
    local overall_status=0
    
    check_certificate_status || overall_status=1
    verify_nginx_ssl_config || overall_status=1
    check_certbot_timer || overall_status=1
    validate_ssl_connection || overall_status=1
    check_ssl_security || overall_status=1
    
    if [[ $overall_status -eq 0 ]]; then
        success "All SSL monitoring checks passed"
    else
        error "Some SSL monitoring checks failed"
    fi
    
    return $overall_status
}

# Function to display help
show_help() {
    echo "FlipSync SSL Certificate Management Script"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  monitor     Run comprehensive SSL monitoring"
    echo "  status      Check certificate status only"
    echo "  renew       Test certificate renewal (dry run)"
    echo "  setup       Set up monitoring cron job"
    echo "  validate    Validate SSL connections"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 monitor    # Run full monitoring suite"
    echo "  $0 status     # Check certificate expiry"
    echo "  $0 renew      # Test renewal process"
}

# Main function
main() {
    local command="${1:-monitor}"
    
    setup_logging
    
    case "$command" in
        "monitor")
            log "Starting SSL monitoring suite..."
            run_monitoring
            ;;
        "status")
            check_certificate_status
            ;;
        "renew")
            test_certificate_renewal
            ;;
        "setup")
            setup_monitoring_cron
            ;;
        "validate")
            validate_ssl_connection
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

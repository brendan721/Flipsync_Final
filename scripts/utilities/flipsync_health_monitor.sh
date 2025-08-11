#!/bin/bash

# FlipSync Production Health Monitoring Script
# ============================================
# Comprehensive health monitoring for all FlipSync production services

set -e

# Configuration
DOMAIN="www.flipsyncai.com"
API_BASE="https://$DOMAIN/api"
WEBSOCKET_URL="wss://$DOMAIN/ws/flipsync"
LOG_FILE="/var/log/flipsync/health_monitor.log"
ALERT_EMAIL="admin@flipsync.com"
SLACK_WEBHOOK=""  # Add Slack webhook URL if needed

# Health check thresholds
MAX_RESPONSE_TIME=5000  # milliseconds
MIN_DISK_SPACE=20       # percentage
MAX_CPU_USAGE=80        # percentage
MAX_MEMORY_USAGE=85     # percentage

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health status tracking
OVERALL_HEALTH="HEALTHY"
FAILED_CHECKS=()
WARNING_CHECKS=()

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
    OVERALL_HEALTH="CRITICAL"
    FAILED_CHECKS+=("$message")
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
    if [[ "$OVERALL_HEALTH" == "HEALTHY" ]]; then
        OVERALL_HEALTH="WARNING"
    fi
    WARNING_CHECKS+=("$message")
}

# Function to setup logging
setup_logging() {
    mkdir -p /var/log/flipsync
    touch "$LOG_FILE"
}

# Function to check system resources
check_system_resources() {
    log "Checking system resources..."
    
    # Check disk space
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    local available_space=$((100 - disk_usage))
    
    if [[ $available_space -lt $MIN_DISK_SPACE ]]; then
        error "Low disk space: ${available_space}% available (threshold: ${MIN_DISK_SPACE}%)"
    else
        success "Disk space OK: ${available_space}% available"
    fi
    
    # Check CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    local cpu_percent=$(echo "$cpu_usage" | cut -d'.' -f1)
    
    if [[ $cpu_percent -gt $MAX_CPU_USAGE ]]; then
        warning "High CPU usage: ${cpu_percent}% (threshold: ${MAX_CPU_USAGE}%)"
    else
        success "CPU usage OK: ${cpu_percent}%"
    fi
    
    # Check memory usage
    local memory_info=$(free | grep Mem)
    local total_mem=$(echo $memory_info | awk '{print $2}')
    local used_mem=$(echo $memory_info | awk '{print $3}')
    local memory_percent=$((used_mem * 100 / total_mem))
    
    if [[ $memory_percent -gt $MAX_MEMORY_USAGE ]]; then
        warning "High memory usage: ${memory_percent}% (threshold: ${MAX_MEMORY_USAGE}%)"
    else
        success "Memory usage OK: ${memory_percent}%"
    fi
}

# Function to check nginx service
check_nginx_service() {
    log "Checking nginx service..."
    
    if systemctl is-active --quiet nginx; then
        success "Nginx service is running"
        
        # Check nginx configuration
        if nginx -t 2>/dev/null; then
            success "Nginx configuration is valid"
        else
            error "Nginx configuration has errors"
        fi
    else
        error "Nginx service is not running"
    fi
}

# Function to check backend service
check_backend_service() {
    log "Checking backend service..."
    
    local backend_pid=$(pgrep -f "uvicorn.*fs_agt_clean" || echo "")
    
    if [[ -n "$backend_pid" ]]; then
        success "Backend service is running (PID: $backend_pid)"
        
        # Check backend memory usage
        local backend_memory=$(ps -p $backend_pid -o %mem --no-headers 2>/dev/null | tr -d ' ' || echo "0")
        log "Backend memory usage: ${backend_memory}%"
        
        if (( $(echo "$backend_memory > 50" | bc -l) )); then
            warning "Backend using high memory: ${backend_memory}%"
        fi
    else
        error "Backend service is not running"
    fi
}

# Function to check database connectivity
check_database_connectivity() {
    log "Checking database connectivity..."
    
    # Test PostgreSQL connection
    if command -v psql >/dev/null 2>&1; then
        if PGPASSWORD="FlipSync_DB_Prod_2024_Secure_Key_9x7z" psql -h 192.168.110.71 -U postgres -d flipsync_agentic_test -c "SELECT 1;" >/dev/null 2>&1; then
            success "PostgreSQL database is accessible"
        else
            error "PostgreSQL database connection failed"
        fi
    else
        warning "psql not available - skipping database connectivity test"
    fi
    
    # Test Redis connection
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli -h 127.0.0.1 -p 6379 ping >/dev/null 2>&1; then
            success "Redis is accessible"
        else
            error "Redis connection failed"
        fi
    else
        warning "redis-cli not available - skipping Redis connectivity test"
    fi
}

# Function to check web application
check_web_application() {
    log "Checking web application..."
    
    local start_time=$(date +%s%3N)
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://$DOMAIN" 2>/dev/null || echo "000")
    local end_time=$(date +%s%3N)
    local response_time=$((end_time - start_time))
    
    if [[ "$response_code" == "200" ]]; then
        success "Web application is accessible (HTTP $response_code, ${response_time}ms)"
        
        if [[ $response_time -gt $MAX_RESPONSE_TIME ]]; then
            warning "Web application response time is slow: ${response_time}ms"
        fi
    else
        error "Web application not accessible (HTTP $response_code)"
    fi
}

# Function to check API endpoints
check_api_endpoints() {
    log "Checking API endpoints..."
    
    # Test main API endpoint
    local api_response=$(curl -s --max-time 10 "$API_BASE/" 2>/dev/null || echo "")
    
    if echo "$api_response" | grep -q "FlipSync API"; then
        success "API root endpoint is responding"
    else
        error "API root endpoint not responding correctly"
    fi
    
    # Test CORS functionality
    local cors_header=$(curl -s -H "Origin: https://$DOMAIN" -H "Access-Control-Request-Method: GET" -X OPTIONS "$API_BASE/" -I 2>/dev/null | grep -i "access-control-allow-origin" || echo "")
    
    if [[ -n "$cors_header" ]]; then
        success "CORS configuration is working"
    else
        warning "CORS configuration may have issues"
    fi
}

# Function to check SSL certificate
check_ssl_certificate() {
    log "Checking SSL certificate..."
    
    local cert_info=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")
    
    if [[ -n "$cert_info" ]]; then
        success "SSL certificate is valid"
        
        # Check certificate expiry
        local expiry_date=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || echo "0")
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [[ $days_until_expiry -lt 30 ]]; then
            warning "SSL certificate expires in $days_until_expiry days"
        else
            success "SSL certificate valid for $days_until_expiry days"
        fi
    else
        error "SSL certificate validation failed"
    fi
}

# Function to send alerts
send_alerts() {
    if [[ "$OVERALL_HEALTH" != "HEALTHY" ]]; then
        local alert_message="FlipSync Health Alert - Status: $OVERALL_HEALTH"
        
        if [[ ${#FAILED_CHECKS[@]} -gt 0 ]]; then
            alert_message+="\n\nFailed Checks:"
            for check in "${FAILED_CHECKS[@]}"; do
                alert_message+="\n- $check"
            done
        fi
        
        if [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
            alert_message+="\n\nWarning Checks:"
            for check in "${WARNING_CHECKS[@]}"; do
                alert_message+="\n- $check"
            done
        fi
        
        # Log alert
        log "ALERT: $alert_message"
        
        # Send email alert (if mail is configured)
        if command -v mail >/dev/null 2>&1 && [[ -n "$ALERT_EMAIL" ]]; then
            echo -e "$alert_message" | mail -s "FlipSync Health Alert - $OVERALL_HEALTH" "$ALERT_EMAIL"
        fi
        
        # Send Slack alert (if webhook is configured)
        if [[ -n "$SLACK_WEBHOOK" ]]; then
            curl -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"$alert_message\"}" \
                "$SLACK_WEBHOOK" >/dev/null 2>&1 || true
        fi
    fi
}

# Function to run all health checks
run_health_checks() {
    log "Starting FlipSync health monitoring..."
    
    check_system_resources
    check_nginx_service
    check_backend_service
    check_database_connectivity
    check_web_application
    check_api_endpoints
    check_ssl_certificate
    
    log "Health monitoring completed - Overall status: $OVERALL_HEALTH"
}

# Function to display health summary
display_health_summary() {
    echo ""
    log "HEALTH MONITORING SUMMARY"
    echo "========================="
    echo ""
    
    case "$OVERALL_HEALTH" in
        "HEALTHY")
            success "🟢 System Status: HEALTHY - All checks passed"
            ;;
        "WARNING")
            warning "🟡 System Status: WARNING - Some issues detected"
            ;;
        "CRITICAL")
            error "🔴 System Status: CRITICAL - Immediate attention required"
            ;;
    esac
    
    echo ""
    echo "📊 Check Results:"
    echo "   ✅ Passed: $(($(echo "${FAILED_CHECKS[@]} ${WARNING_CHECKS[@]}" | wc -w) == 0 ? 7 : 7 - ${#FAILED_CHECKS[@]} - ${#WARNING_CHECKS[@]}))"
    echo "   ⚠️ Warnings: ${#WARNING_CHECKS[@]}"
    echo "   ❌ Failed: ${#FAILED_CHECKS[@]}"
    
    if [[ ${#FAILED_CHECKS[@]} -gt 0 ]] || [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
        echo ""
        echo "🔧 Recommended Actions:"
        if [[ ${#FAILED_CHECKS[@]} -gt 0 ]]; then
            echo "   - Investigate and resolve failed checks immediately"
        fi
        if [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
            echo "   - Monitor warning conditions and plan maintenance"
        fi
    fi
}

# Function to show help
show_help() {
    echo "FlipSync Health Monitoring Script"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  monitor     Run comprehensive health monitoring (default)"
    echo "  quick       Run quick health check"
    echo "  setup       Set up monitoring cron job"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 monitor    # Run full health monitoring"
    echo "  $0 quick      # Run quick health check"
    echo "  $0 setup      # Set up automated monitoring"
}

# Main function
main() {
    local command="${1:-monitor}"
    
    setup_logging
    
    case "$command" in
        "monitor")
            run_health_checks
            send_alerts
            display_health_summary
            ;;
        "quick")
            check_nginx_service
            check_backend_service
            check_web_application
            display_health_summary
            ;;
        "setup")
            # Add cron job for health monitoring
            local cron_job="*/15 * * * * /opt/flipsync/flipsync_health_monitor.sh quick >> /var/log/flipsync/health_cron.log 2>&1"
            if ! crontab -l 2>/dev/null | grep -q "flipsync_health_monitor.sh"; then
                (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
                success "Health monitoring cron job added (every 15 minutes)"
            else
                log "Health monitoring cron job already exists"
            fi
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
    
    # Exit with error code if health is critical
    if [[ "$OVERALL_HEALTH" == "CRITICAL" ]]; then
        exit 1
    fi
}

# Run main function
main "$@"

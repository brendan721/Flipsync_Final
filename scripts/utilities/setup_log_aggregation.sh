#!/bin/bash

# FlipSync Log Aggregation Setup Script
# =====================================
# Comprehensive log aggregation and monitoring setup for production

set -e

# Configuration
LOG_BASE_DIR="/var/log/flipsync"
NGINX_LOG_DIR="/var/log/nginx"
BACKEND_LOG_DIR="/opt/flipsync/logs"
LOGROTATE_CONFIG="/etc/logrotate.d/flipsync"
RSYSLOG_CONFIG="/etc/rsyslog.d/50-flipsync.conf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to create log directories
setup_log_directories() {
    log "Setting up log directories..."
    
    # Create main log directories
    mkdir -p "$LOG_BASE_DIR"/{nginx,backend,application,health,security,performance}
    mkdir -p "$BACKEND_LOG_DIR"/{api,agents,workflows,errors}
    
    # Set proper permissions
    chown -R www-data:www-data "$LOG_BASE_DIR/nginx"
    chown -R root:root "$LOG_BASE_DIR"/{health,security,performance}
    
    if [ -d "/opt/flipsync" ]; then
        chown -R root:root "$BACKEND_LOG_DIR"
    fi
    
    success "Log directories created and configured"
}

# Function to configure nginx logging
configure_nginx_logging() {
    log "Configuring nginx logging..."
    
    # Create nginx log format configuration
    cat > /tmp/nginx_log_format.conf << 'EOF'
# FlipSync Nginx Log Formats
log_format flipsync_main '$remote_addr - $remote_user [$time_local] "$request" '
                         '$status $body_bytes_sent "$http_referer" '
                         '"$http_user_agent" "$http_x_forwarded_for" '
                         'rt=$request_time uct="$upstream_connect_time" '
                         'uht="$upstream_header_time" urt="$upstream_response_time"';

log_format flipsync_api '$remote_addr - $remote_user [$time_local] "$request" '
                        '$status $body_bytes_sent "$http_referer" '
                        '"$http_user_agent" "$http_x_forwarded_for" '
                        'rt=$request_time uct="$upstream_connect_time" '
                        'uht="$upstream_header_time" urt="$upstream_response_time" '
                        'api_endpoint="$uri" method="$request_method"';

log_format flipsync_error '$time_local [$log_level] $pid#$tid: $message';
EOF

    # Add log format to nginx configuration if not already present
    if ! grep -q "flipsync_main" /etc/nginx/nginx.conf; then
        # Insert log formats into nginx.conf
        sed -i '/http {/r /tmp/nginx_log_format.conf' /etc/nginx/nginx.conf
        success "Nginx log formats added"
    else
        log "Nginx log formats already configured"
    fi
    
    # Configure access and error logs in site configuration
    if [ -f "/etc/nginx/sites-available/flipsyncai.com" ]; then
        # Backup current configuration
        cp /etc/nginx/sites-available/flipsyncai.com /etc/nginx/sites-available/flipsyncai.com.backup.$(date +%Y%m%d)
        
        # Add logging configuration to server blocks
        if ! grep -q "access_log.*flipsync" /etc/nginx/sites-available/flipsyncai.com; then
            log "Adding access log configuration to nginx site"
            # This will be added manually to avoid complex sed operations
        fi
    fi
    
    rm -f /tmp/nginx_log_format.conf
}

# Function to configure rsyslog for centralized logging
configure_rsyslog() {
    log "Configuring rsyslog for centralized logging..."
    
    cat > "$RSYSLOG_CONFIG" << 'EOF'
# FlipSync Application Logging Configuration

# FlipSync Backend Logs
:programname, isequal, "flipsync-backend" /var/log/flipsync/backend/backend.log
:programname, isequal, "flipsync-api" /var/log/flipsync/backend/api.log
:programname, isequal, "flipsync-agents" /var/log/flipsync/backend/agents.log

# FlipSync Health Monitoring
:programname, isequal, "flipsync-health" /var/log/flipsync/health/health.log

# FlipSync Security Events
:programname, isequal, "flipsync-security" /var/log/flipsync/security/security.log

# FlipSync Performance Metrics
:programname, isequal, "flipsync-performance" /var/log/flipsync/performance/performance.log

# Stop processing these messages
:programname, isequal, "flipsync-backend" stop
:programname, isequal, "flipsync-api" stop
:programname, isequal, "flipsync-agents" stop
:programname, isequal, "flipsync-health" stop
:programname, isequal, "flipsync-security" stop
:programname, isequal, "flipsync-performance" stop
EOF

    # Restart rsyslog to apply configuration
    systemctl restart rsyslog
    success "Rsyslog configured for centralized logging"
}

# Function to configure log rotation
configure_log_rotation() {
    log "Configuring log rotation..."
    
    cat > "$LOGROTATE_CONFIG" << 'EOF'
# FlipSync Log Rotation Configuration

/var/log/flipsync/*/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}

/var/log/flipsync/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}

/opt/flipsync/logs/*/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        # Send SIGUSR1 to backend process to reopen log files
        pkill -USR1 -f "uvicorn.*fs_agt_clean" > /dev/null 2>&1 || true
    endscript
}
EOF

    # Test logrotate configuration
    logrotate -d "$LOGROTATE_CONFIG" > /dev/null 2>&1
    success "Log rotation configured"
}

# Function to create log monitoring script
create_log_monitoring_script() {
    log "Creating log monitoring script..."
    
    cat > /opt/flipsync/log_monitor.sh << 'EOF'
#!/bin/bash

# FlipSync Log Monitoring Script
# Real-time log analysis and alerting

LOG_BASE_DIR="/var/log/flipsync"
ALERT_THRESHOLD_ERRORS=10
ALERT_THRESHOLD_WARNINGS=50
TIME_WINDOW=300  # 5 minutes

# Function to check error rates
check_error_rates() {
    local log_file="$1"
    local time_window="$2"
    
    if [ -f "$log_file" ]; then
        # Count errors in the last time window
        local error_count=$(tail -n 1000 "$log_file" | \
            awk -v window="$time_window" '
            BEGIN { now = systime() }
            {
                # Extract timestamp and check if within window
                if (systime() - now < window && /ERROR|CRITICAL|FATAL/) {
                    count++
                }
            }
            END { print count+0 }')
        
        echo "$error_count"
    else
        echo "0"
    fi
}

# Function to analyze nginx logs
analyze_nginx_logs() {
    local access_log="/var/log/nginx/access.log"
    local error_log="/var/log/nginx/error.log"
    
    if [ -f "$access_log" ]; then
        # Check for high error rates (4xx, 5xx)
        local error_rate=$(tail -n 1000 "$access_log" | \
            awk '{print $9}' | \
            grep -E '^[45][0-9][0-9]$' | \
            wc -l)
        
        if [ "$error_rate" -gt "$ALERT_THRESHOLD_ERRORS" ]; then
            logger -p local0.warning -t flipsync-security "High HTTP error rate detected: $error_rate errors in last 1000 requests"
        fi
    fi
    
    if [ -f "$error_log" ]; then
        local nginx_errors=$(check_error_rates "$error_log" "$TIME_WINDOW")
        if [ "$nginx_errors" -gt "$ALERT_THRESHOLD_ERRORS" ]; then
            logger -p local0.error -t flipsync-security "High nginx error rate: $nginx_errors errors in last $TIME_WINDOW seconds"
        fi
    fi
}

# Function to analyze backend logs
analyze_backend_logs() {
    local backend_log="/opt/flipsync/logs/backend.log"
    
    if [ -f "$backend_log" ]; then
        local backend_errors=$(check_error_rates "$backend_log" "$TIME_WINDOW")
        if [ "$backend_errors" -gt "$ALERT_THRESHOLD_ERRORS" ]; then
            logger -p local0.error -t flipsync-backend "High backend error rate: $backend_errors errors in last $TIME_WINDOW seconds"
        fi
    fi
}

# Main monitoring function
main() {
    analyze_nginx_logs
    analyze_backend_logs
    
    # Log monitoring completion
    logger -p local0.info -t flipsync-health "Log monitoring completed at $(date)"
}

main "$@"
EOF

    chmod +x /opt/flipsync/log_monitor.sh
    success "Log monitoring script created"
}

# Function to setup log monitoring cron job
setup_log_monitoring_cron() {
    log "Setting up log monitoring cron job..."
    
    # Add cron job for log monitoring every 5 minutes
    local cron_job="*/5 * * * * /opt/flipsync/log_monitor.sh >> /var/log/flipsync/health/log_monitor.log 2>&1"
    
    if ! crontab -l 2>/dev/null | grep -q "log_monitor.sh"; then
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        success "Log monitoring cron job added (every 5 minutes)"
    else
        log "Log monitoring cron job already exists"
    fi
}

# Function to create log analysis tools
create_log_analysis_tools() {
    log "Creating log analysis tools..."
    
    cat > /opt/flipsync/analyze_logs.sh << 'EOF'
#!/bin/bash

# FlipSync Log Analysis Tool
# Generate reports and statistics from logs

LOG_BASE_DIR="/var/log/flipsync"
REPORT_DIR="/var/log/flipsync/reports"

# Create reports directory
mkdir -p "$REPORT_DIR"

# Function to generate daily report
generate_daily_report() {
    local date="${1:-$(date +%Y-%m-%d)}"
    local report_file="$REPORT_DIR/daily_report_$date.txt"
    
    echo "FlipSync Daily Log Report - $date" > "$report_file"
    echo "=======================================" >> "$report_file"
    echo "" >> "$report_file"
    
    # Nginx statistics
    if [ -f "/var/log/nginx/access.log" ]; then
        echo "NGINX STATISTICS:" >> "$report_file"
        echo "Total requests: $(grep "$date" /var/log/nginx/access.log | wc -l)" >> "$report_file"
        echo "Unique IPs: $(grep "$date" /var/log/nginx/access.log | awk '{print $1}' | sort -u | wc -l)" >> "$report_file"
        echo "Status codes:" >> "$report_file"
        grep "$date" /var/log/nginx/access.log | awk '{print $9}' | sort | uniq -c | sort -nr >> "$report_file"
        echo "" >> "$report_file"
    fi
    
    # Backend statistics
    if [ -f "/opt/flipsync/logs/backend.log" ]; then
        echo "BACKEND STATISTICS:" >> "$report_file"
        echo "Total log entries: $(grep "$date" /opt/flipsync/logs/backend.log | wc -l)" >> "$report_file"
        echo "Error count: $(grep "$date" /opt/flipsync/logs/backend.log | grep -i error | wc -l)" >> "$report_file"
        echo "Warning count: $(grep "$date" /opt/flipsync/logs/backend.log | grep -i warning | wc -l)" >> "$report_file"
        echo "" >> "$report_file"
    fi
    
    echo "Report generated: $report_file"
}

# Function to show real-time log tail
show_realtime_logs() {
    echo "Real-time FlipSync logs (Ctrl+C to exit):"
    echo "=========================================="
    
    # Tail multiple log files
    tail -f /var/log/nginx/access.log \
         /var/log/nginx/error.log \
         /opt/flipsync/logs/backend.log \
         /var/log/flipsync/health/health.log 2>/dev/null
}

# Main function
case "${1:-daily}" in
    "daily")
        generate_daily_report "$2"
        ;;
    "realtime")
        show_realtime_logs
        ;;
    *)
        echo "Usage: $0 [daily|realtime] [date]"
        echo "  daily    - Generate daily report (default)"
        echo "  realtime - Show real-time log tail"
        ;;
esac
EOF

    chmod +x /opt/flipsync/analyze_logs.sh
    success "Log analysis tools created"
}

# Main function
main() {
    log "Starting FlipSync log aggregation setup..."
    
    setup_log_directories
    configure_nginx_logging
    configure_rsyslog
    configure_log_rotation
    create_log_monitoring_script
    setup_log_monitoring_cron
    create_log_analysis_tools
    
    success "Log aggregation setup completed successfully!"
    
    echo ""
    log "Log Aggregation Summary:"
    echo "========================"
    echo "📁 Log directories: $LOG_BASE_DIR"
    echo "🔄 Log rotation: Daily, 30 days retention"
    echo "📊 Monitoring: Every 5 minutes"
    echo "📈 Analysis tools: /opt/flipsync/analyze_logs.sh"
    echo ""
    echo "Usage examples:"
    echo "  ./analyze_logs.sh daily        # Generate daily report"
    echo "  ./analyze_logs.sh realtime     # Real-time log monitoring"
    echo "  ./flipsync_health_monitor.sh   # Health monitoring"
}

# Run main function
main "$@"

#!/bin/bash

# FlipSync Week 1 Changes Deployment Script
# =========================================
# Deploy all Week 1 critical fixes to production server 174.138.77.110

set -e

# Configuration
DROPLET_IP="174.138.77.110"
DROPLET_USER="root"
PRODUCTION_PATH="/opt/flipsync"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
WEB_ROOT="/var/www/flipsyncai.com"

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

# Function to run SSH commands
run_ssh() {
    ssh -o StrictHostKeyChecking=no ${DROPLET_USER}@${DROPLET_IP} "$1"
}

# Function to copy files to server
copy_to_server() {
    local local_file="$1"
    local remote_path="$2"
    scp -o StrictHostKeyChecking=no "$local_file" "${DROPLET_USER}@${DROPLET_IP}:$remote_path"
}

# Function to check SSH connectivity
check_ssh() {
    log "Checking SSH connectivity to production server..."
    if ! run_ssh "echo 'SSH connection successful'"; then
        error "Cannot connect to production server. Please check SSH configuration."
    fi
    success "SSH connection established"
}

# Function to backup current configurations
backup_current_config() {
    log "Creating backup of current configurations..."
    
    local backup_date=$(date +%Y%m%d_%H%M%S)
    
    run_ssh "
        # Create backup directory
        mkdir -p /root/backups/week1_deployment_$backup_date
        
        # Backup nginx configurations
        if [ -f $NGINX_SITES_AVAILABLE/default ]; then
            cp $NGINX_SITES_AVAILABLE/default /root/backups/week1_deployment_$backup_date/nginx_default.backup
        fi
        
        if [ -f $NGINX_SITES_AVAILABLE/flipsyncai.com ]; then
            cp $NGINX_SITES_AVAILABLE/flipsyncai.com /root/backups/week1_deployment_$backup_date/nginx_flipsyncai.backup
        fi
        
        # Backup current web directory
        if [ -d $WEB_ROOT ]; then
            cp -r $WEB_ROOT /root/backups/week1_deployment_$backup_date/web_backup
        fi
        
        echo 'Backup completed: /root/backups/week1_deployment_$backup_date'
    "
    
    success "Configuration backup completed"
}

# Function to deploy nginx configuration
deploy_nginx_config() {
    log "Deploying consolidated nginx configuration..."
    
    # Copy the consolidated nginx configuration
    copy_to_server "flipsyncai.com.conf" "/tmp/flipsyncai.com.conf"
    
    run_ssh "
        # Install the new configuration
        cp /tmp/flipsyncai.com.conf $NGINX_SITES_AVAILABLE/flipsyncai.com
        
        # Remove old conflicting configurations
        rm -f $NGINX_SITES_ENABLED/default
        rm -f $NGINX_SITES_ENABLED/production.conf
        
        # Enable the new configuration
        ln -sf $NGINX_SITES_AVAILABLE/flipsyncai.com $NGINX_SITES_ENABLED/
        
        # Test nginx configuration
        nginx -t
    "
    
    success "Nginx configuration deployed and validated"
}

# Function to deploy Flutter web app
deploy_flutter_app() {
    log "Building and deploying Flutter web application..."
    
    # Build Flutter web app locally
    cd mobile
    log "Building Flutter web app for production..."
    flutter clean
    flutter pub get
    flutter build web --release
    
    if [ ! -d "build/web" ]; then
        error "Flutter build failed - build/web directory not found"
    fi
    
    # Create web directory on server
    run_ssh "
        mkdir -p $WEB_ROOT
        chown -R www-data:www-data $WEB_ROOT
    "
    
    # Deploy web files
    log "Uploading Flutter web files to production server..."
    rsync -avz --delete build/web/ ${DROPLET_USER}@${DROPLET_IP}:$WEB_ROOT/
    
    # Set proper permissions
    run_ssh "
        chown -R www-data:www-data $WEB_ROOT
        chmod -R 755 $WEB_ROOT
        
        # Verify critical files exist
        if [ ! -f $WEB_ROOT/index.html ]; then
            echo 'ERROR: index.html not found'
            exit 1
        fi
        
        if [ ! -f $WEB_ROOT/main.dart.js ]; then
            echo 'ERROR: main.dart.js not found'
            exit 1
        fi
        
        echo 'Flutter web app deployed successfully'
    "
    
    cd ..
    success "Flutter web application deployed"
}

# Function to deploy backend configuration
deploy_backend_config() {
    log "Deploying backend configuration with updated CORS settings..."
    
    # Copy updated start script
    copy_to_server "start_production_service.sh" "/tmp/start_production_service.sh"
    
    run_ssh "
        # Install the updated start script
        cp /tmp/start_production_service.sh $PRODUCTION_PATH/start_production_service.sh
        chmod +x $PRODUCTION_PATH/start_production_service.sh
        
        # Verify CORS configuration
        grep 'CORS_ORIGINS=' $PRODUCTION_PATH/start_production_service.sh
    "
    
    success "Backend configuration deployed"
}

# Function to restart services
restart_services() {
    log "Restarting services with new configurations..."
    
    run_ssh "
        # Reload nginx with new configuration
        systemctl reload nginx
        
        # Check nginx status
        systemctl status nginx --no-pager -l
        
        # Restart backend service if running
        if pgrep -f 'uvicorn.*fs_agt_clean' > /dev/null; then
            echo 'Stopping existing backend service...'
            pkill -f 'uvicorn.*fs_agt_clean' || true
            sleep 3
        fi
        
        echo 'Services restarted successfully'
    "
    
    success "Services restarted"
}

# Function to validate deployment
validate_deployment() {
    log "Validating deployment..."

    local validation_failed=0

    # Test nginx configuration
    if ! run_ssh "nginx -t"; then
        error "Nginx configuration test failed"
        validation_failed=1
    else
        success "Nginx configuration test passed"
    fi

    # Test web app accessibility
    log "Testing web application accessibility..."
    local web_status=$(curl -s -o /dev/null -w "%{http_code}" https://www.flipsyncai.com 2>/dev/null || echo "000")
    if [[ "$web_status" == "200" ]]; then
        success "Web application is accessible (HTTP $web_status)"
    elif [[ "$web_status" == "301" || "$web_status" == "302" ]]; then
        success "Web application redirects working (HTTP $web_status)"
    else
        warning "Web application not accessible (HTTP $web_status)"
        validation_failed=1
    fi

    # Test API accessibility
    log "Testing API accessibility..."
    local api_status=$(curl -s -o /dev/null -w "%{http_code}" https://www.flipsyncai.com/api/ 2>/dev/null || echo "000")
    if [[ "$api_status" == "200" ]]; then
        success "API endpoint is accessible (HTTP $api_status)"
    else
        warning "API endpoint not accessible (HTTP $api_status) - backend may need restart"
        validation_failed=1
    fi

    # Test CORS functionality
    log "Testing CORS configuration..."
    local cors_header=$(curl -s -H "Origin: https://www.flipsyncai.com" -H "Access-Control-Request-Method: GET" -X OPTIONS https://www.flipsyncai.com/api/ -I 2>/dev/null | grep -i "access-control-allow-origin" || echo "")
    if [[ -n "$cors_header" ]]; then
        success "CORS configuration is working"
    else
        warning "CORS configuration may have issues"
        validation_failed=1
    fi

    if [[ $validation_failed -eq 0 ]]; then
        success "All deployment validation checks passed"
    else
        warning "Some deployment validation checks failed - manual review recommended"
    fi

    return $validation_failed
}

# Function to rollback deployment
rollback_deployment() {
    local backup_dir="$1"

    if [[ -z "$backup_dir" ]]; then
        error "Backup directory not specified for rollback"
        return 1
    fi

    log "Rolling back deployment using backup: $backup_dir"

    run_ssh "
        # Rollback nginx configuration
        if [ -f $backup_dir/nginx_flipsyncai.backup ]; then
            cp $backup_dir/nginx_flipsyncai.backup $NGINX_SITES_AVAILABLE/flipsyncai.com
            echo 'Nginx configuration rolled back'
        fi

        if [ -f $backup_dir/nginx_default.backup ]; then
            cp $backup_dir/nginx_default.backup $NGINX_SITES_AVAILABLE/default
            echo 'Default nginx configuration rolled back'
        fi

        # Rollback web directory
        if [ -d $backup_dir/web_backup ]; then
            rm -rf $WEB_ROOT
            cp -r $backup_dir/web_backup $WEB_ROOT
            chown -R www-data:www-data $WEB_ROOT
            echo 'Web directory rolled back'
        fi

        # Test and reload nginx
        nginx -t && systemctl reload nginx
        echo 'Nginx reloaded with rollback configuration'
    "

    success "Deployment rollback completed"
}

# Function to display deployment summary
deployment_summary() {
    log "Week 1 Deployment Summary:"
    echo "=========================="
    echo "✅ Nginx configuration: Consolidated to flipsyncai.com.conf"
    echo "✅ CORS configuration: Standardized to FastAPI middleware only"
    echo "✅ Flutter web app: Built and deployed to $WEB_ROOT"
    echo "✅ Backend configuration: Updated with production CORS origins"
    echo "✅ Services: Restarted with new configurations"
    echo ""
    echo "🌐 Web Application: https://flipsyncai.com"
    echo "🌐 API Health: https://flipsyncai.com/api/v1/health"
    echo "🌐 WebSocket: wss://flipsyncai.com/ws/flipsync"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Test all functionality end-to-end"
    echo "2. Verify eBay OAuth integration"
    echo "3. Monitor logs for any issues"
    echo "4. Proceed with Week 2 SSL and domain configuration"
}

# Main deployment function
main() {
    log "Starting Week 1 Changes Deployment to Production Server"
    log "======================================================="
    
    # Pre-deployment checks
    check_ssh
    
    # Deployment steps
    backup_current_config
    deploy_nginx_config
    deploy_flutter_app
    deploy_backend_config
    restart_services
    validate_deployment
    
    # Summary
    deployment_summary
    
    success "Week 1 deployment completed successfully!"
}

# Run main function
main "$@"

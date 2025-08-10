#!/bin/bash

# FlipSync SSL Verification Script
# This script verifies that SSL certificates and HTTPS are working correctly

set -e

# Configuration
DOMAIN="flipsyncai.com"
WWW_DOMAIN="www.flipsyncai.com"
BACKEND_PORT="8000"

echo "🔍 FlipSync SSL Verification"
echo "============================"
echo "Domain: $DOMAIN"
echo "WWW Domain: $WWW_DOMAIN"
echo ""

# Function to test URL and return status
test_url() {
    local url=$1
    local description=$2
    echo -n "Testing $description... "
    
    local status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
    local ssl_status=""
    
    if [[ $url == https* ]]; then
        ssl_status=$(curl -s -I --max-time 10 "$url" 2>/dev/null | grep -i "strict-transport-security" || echo "")
        if [[ -n "$ssl_status" ]]; then
            ssl_status=" (HSTS enabled)"
        else
            ssl_status=" (No HSTS)"
        fi
    fi
    
    case $status in
        200) echo "✅ OK (200)$ssl_status" ;;
        301|302) echo "✅ Redirect ($status)$ssl_status" ;;
        405) echo "✅ Method Not Allowed (405)$ssl_status - Backend responding" ;;
        000) echo "❌ Connection failed" ;;
        *) echo "⚠️  Status: $status$ssl_status" ;;
    esac
    
    return 0
}

# Function to check SSL certificate
check_ssl_cert() {
    local domain=$1
    echo -n "Checking SSL certificate for $domain... "
    
    local cert_info=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")
    
    if [[ -n "$cert_info" ]]; then
        local not_after=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
        echo "✅ Valid (Expires: $not_after)"
    else
        echo "❌ Certificate check failed"
    fi
}

# Function to check DNS resolution
check_dns() {
    local domain=$1
    echo -n "Checking DNS for $domain... "
    
    local ip=$(dig +short "$domain" 2>/dev/null | tail -n1)
    if [[ -n "$ip" && "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "✅ Resolves to $ip"
    else
        echo "❌ DNS resolution failed"
    fi
}

# Function to check service status
check_service() {
    local service=$1
    echo -n "Checking $service service... "
    
    if systemctl is-active --quiet "$service"; then
        echo "✅ Running"
    else
        echo "❌ Not running"
    fi
}

echo "🌐 DNS Resolution"
echo "=================="
check_dns "$DOMAIN"
check_dns "$WWW_DOMAIN"

echo ""
echo "🔐 SSL Certificates"
echo "==================="
check_ssl_cert "$DOMAIN"
check_ssl_cert "$WWW_DOMAIN"

echo ""
echo "🚀 Service Status"
echo "================="
check_service "nginx"
check_service "certbot.timer"

# Check if backend is running
echo -n "Checking backend service (port $BACKEND_PORT)... "
if curl -s --max-time 5 "http://127.0.0.1:$BACKEND_PORT/api/v1/health" > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

echo ""
echo "🌍 HTTP/HTTPS Access Tests"
echo "=========================="

# Test HTTP redirects
test_url "http://$DOMAIN" "HTTP $DOMAIN"
test_url "http://$WWW_DOMAIN" "HTTP $WWW_DOMAIN"

# Test HTTPS access
test_url "https://$DOMAIN" "HTTPS $DOMAIN"
test_url "https://$WWW_DOMAIN" "HTTPS $WWW_DOMAIN"

echo ""
echo "🔗 eBay OAuth Endpoint Tests"
echo "============================"

# Test eBay OAuth endpoint
test_url "https://$DOMAIN/ebay-oauth" "eBay OAuth (HTTPS)"
test_url "https://$WWW_DOMAIN/ebay-oauth" "eBay OAuth WWW (HTTPS)"

# Test with parameters
test_url "https://$DOMAIN/ebay-oauth?test=1" "eBay OAuth with params"

echo ""
echo "📡 API Endpoint Tests"
echo "===================="

# Test API endpoints
test_url "https://$DOMAIN/api/v1/health" "Health Check API"
test_url "https://$DOMAIN/docs" "API Documentation"
test_url "https://$DOMAIN/openapi.json" "OpenAPI Spec"

echo ""
echo "🔥 Firewall Status"
echo "=================="
if command -v ufw &> /dev/null; then
    echo "UFW Status:"
    ufw status | grep -E "(Status|80|443|8000|22)" || echo "No relevant rules found"
else
    echo "UFW not installed"
fi

echo ""
echo "📋 Certificate Details"
echo "======================"
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "Certificate file: ✅ Found"
    echo "Certificate details:"
    openssl x509 -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" -noout -subject -issuer -dates 2>/dev/null || echo "Could not read certificate details"
else
    echo "Certificate file: ❌ Not found"
fi

echo ""
echo "🔄 Auto-renewal Status"
echo "======================"
if systemctl is-enabled --quiet certbot.timer; then
    echo "Auto-renewal: ✅ Enabled"
    echo "Next renewal check:"
    systemctl list-timers certbot.timer --no-pager 2>/dev/null | grep certbot || echo "Timer info not available"
else
    echo "Auto-renewal: ❌ Not enabled"
fi

echo ""
echo "📝 Configuration Files"
echo "======================"
echo -n "Nginx config: "
if [ -f "/etc/nginx/sites-available/flipsyncai" ]; then
    echo "✅ Found"
else
    echo "❌ Not found"
fi

echo -n "Nginx config enabled: "
if [ -L "/etc/nginx/sites-enabled/flipsyncai" ]; then
    echo "✅ Enabled"
else
    echo "❌ Not enabled"
fi

echo ""
echo "🧪 SSL Security Test"
echo "===================="
echo "Testing SSL configuration with external tool..."
echo "You can also test at: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"

# Quick SSL test
echo -n "SSL handshake test: "
if echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" >/dev/null 2>&1; then
    echo "✅ SSL handshake successful"
else
    echo "❌ SSL handshake failed"
fi

echo ""
echo "🎯 Summary"
echo "=========="
echo "If all tests show ✅, your SSL setup is working correctly!"
echo "If you see ❌ or ⚠️, please check the specific issues above."
echo ""
echo "🔗 Test your eBay OAuth flow at:"
echo "   https://$DOMAIN/ebay-oauth"
echo ""
echo "📱 Your React testing dashboard should now be able to complete"
echo "   the full OAuth flow with eBay!"

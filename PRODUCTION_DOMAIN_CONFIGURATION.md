# FlipSync Production Domain Configuration Guide

## 🌐 **DOMAIN-BASED DEPLOYMENT CONFIGURATION**

This guide outlines the proper domain configuration for FlipSync production deployment, replacing hardcoded IP addresses with domain-based URLs for better scalability and maintainability.

## 📋 **REQUIRED DNS CONFIGURATION**

### **Primary Domain**: `flipsyncai.com`

#### **Required DNS Records**:

```dns
# Main application
www.flipsyncai.com    A     174.138.77.110
flipsyncai.com        A     174.138.77.110

# API endpoint
api.flipsyncai.com    A     174.138.77.110

# WebSocket endpoint (can use same as main)
ws.flipsyncai.com     A     174.138.77.110

# Database (if external access needed)
db.flipsyncai.com     A     174.138.77.110

# Redis (if external access needed)
redis.flipsyncai.com  A     174.138.77.110

# CDN/Assets (optional)
cdn.flipsyncai.com    A     174.138.77.110
```

## 🔧 **UPDATED CONFIGURATION**

### **Frontend Configuration** ✅ **FIXED**

**File**: `mobile/lib/core/config/environment.dart`

```dart
// Production URLs - Now domain-based
static String get apiBaseUrl =>
    _config['API_BASE_URL'] as String? ??
    (_environment == Environment.prod ? 'https://www.flipsyncai.com' : 'http://localhost:8000');

static String get wsBaseUrl =>
    _config['WS_BASE_URL'] as String? ??
    (_environment == Environment.prod ? 'wss://www.flipsyncai.com' : 'ws://localhost:8000');

// Production defaults
'API_BASE_URL': 'https://www.flipsyncai.com',
'WS_BASE_URL': 'wss://www.flipsyncai.com',
'WEBSOCKET_URL': 'wss://www.flipsyncai.com/ws/flipsync',
'DB_HOST': 'db.flipsyncai.com',
'REDIS_HOST': 'redis.flipsyncai.com',
```

### **Backend Configuration** (Recommended Updates)

**File**: `fs_agt_clean/core/config/production_config.py`

```python
# Recommended domain-based configuration
ALLOWED_HOSTS = [
    'www.flipsyncai.com',
    'flipsyncai.com',
    'api.flipsyncai.com',
    '174.138.77.110',  # Keep IP as fallback
]

CORS_ALLOWED_ORIGINS = [
    'https://www.flipsyncai.com',
    'https://flipsyncai.com',
    'https://api.flipsyncai.com',
]

# WebSocket origins
WEBSOCKET_ALLOWED_ORIGINS = [
    'https://www.flipsyncai.com',
    'https://flipsyncai.com',
]
```

## 🔒 **SSL/TLS CONFIGURATION**

### **Required SSL Certificates**:

1. **Wildcard Certificate** (Recommended):
   - `*.flipsyncai.com`
   - Covers all subdomains

2. **Individual Certificates**:
   - `www.flipsyncai.com`
   - `api.flipsyncai.com`
   - `ws.flipsyncai.com`

### **Let's Encrypt Setup** (Free SSL):

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get wildcard certificate
sudo certbot certonly --manual --preferred-challenges=dns \
  -d flipsyncai.com -d *.flipsyncai.com

# Or individual certificates
sudo certbot --nginx -d www.flipsyncai.com -d api.flipsyncai.com
```

## 🌐 **NGINX CONFIGURATION**

### **Recommended Nginx Setup**:

```nginx
# /etc/nginx/sites-available/flipsyncai.com
server {
    listen 80;
    server_name flipsyncai.com www.flipsyncai.com;
    return 301 https://www.flipsyncai.com$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.flipsyncai.com;
    
    ssl_certificate /etc/letsencrypt/live/flipsyncai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/flipsyncai.com/privkey.pem;
    
    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket endpoint
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # Flutter web app
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🚀 **DEPLOYMENT STEPS**

### **1. DNS Configuration**:
```bash
# Configure DNS records at your domain registrar
# Point all required subdomains to 174.138.77.110
```

### **2. SSL Certificate Setup**:
```bash
# Get SSL certificates for the domain
sudo certbot --nginx -d www.flipsyncai.com -d api.flipsyncai.com
```

### **3. Nginx Configuration**:
```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/flipsyncai.com
sudo ln -s /etc/nginx/sites-available/flipsyncai.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### **4. Backend Configuration**:
```bash
# Update backend environment variables
export ALLOWED_HOSTS="www.flipsyncai.com,flipsyncai.com,api.flipsyncai.com"
export CORS_ALLOWED_ORIGINS="https://www.flipsyncai.com,https://flipsyncai.com"
```

### **5. Frontend Build**:
```bash
# Build Flutter web app with production configuration
cd mobile
flutter build web --dart-define=ENVIRONMENT=prod \
  --dart-define=API_BASE_URL=https://www.flipsyncai.com \
  --dart-define=WS_BASE_URL=wss://www.flipsyncai.com
```

## 🔍 **VERIFICATION STEPS**

### **1. DNS Resolution**:
```bash
# Verify DNS records
nslookup www.flipsyncai.com
nslookup api.flipsyncai.com
nslookup ws.flipsyncai.com
```

### **2. SSL Certificate**:
```bash
# Check SSL certificate
openssl s_client -connect www.flipsyncai.com:443 -servername www.flipsyncai.com
```

### **3. API Endpoints**:
```bash
# Test API endpoint
curl -I https://www.flipsyncai.com/api/v1/health

# Test WebSocket endpoint
curl -I https://www.flipsyncai.com/ws/flipsync
```

### **4. Frontend Access**:
```bash
# Test main application
curl -I https://www.flipsyncai.com/
```

## 📊 **BENEFITS OF DOMAIN-BASED DEPLOYMENT**

### **✅ Advantages**:
1. **Professional Appearance**: Clean, branded URLs
2. **SSL/TLS Support**: Proper HTTPS encryption
3. **Load Balancing**: Easy to add multiple servers
4. **CDN Integration**: Better performance with CDNs
5. **Maintenance**: Easier server migrations
6. **SEO Benefits**: Better search engine optimization
7. **Security**: Proper CORS and origin validation

### **🔧 Flexibility**:
- **Server Migration**: Change IP without code changes
- **Load Balancing**: Add multiple backend servers
- **Subdomain Routing**: Route different services to different servers
- **Environment Separation**: dev.flipsyncai.com, staging.flipsyncai.com

## 🚨 **MIGRATION CHECKLIST**

### **Before Migration**:
- [ ] Configure DNS records
- [ ] Obtain SSL certificates
- [ ] Update Nginx configuration
- [ ] Test domain resolution
- [ ] Backup current configuration

### **During Migration**:
- [ ] Update frontend configuration
- [ ] Update backend CORS settings
- [ ] Deploy with new configuration
- [ ] Test all endpoints
- [ ] Verify WebSocket connections

### **After Migration**:
- [ ] Monitor application performance
- [ ] Check SSL certificate expiration
- [ ] Update documentation
- [ ] Notify users of new URLs
- [ ] Set up monitoring for new domains

## 🎯 **CONCLUSION**

The migration from hardcoded IP addresses to domain-based URLs provides:

- **Professional deployment** with proper SSL/TLS
- **Better scalability** and maintenance
- **Improved security** with proper origin validation
- **Future-proof architecture** for growth

**Status**: ✅ **Configuration Updated - Ready for Domain Deployment**

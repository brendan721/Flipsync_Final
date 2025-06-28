# 🚀 FlipSync DigitalOcean Migration Plan

## 🎯 **MISSION: SOLVE ALL SSL/CORS ISSUES WITH PRODUCTION DEPLOYMENT**

**Root Cause Identified**: API container infinite restart loop causing CORS failures
**Solution**: Migrate to www.flipsyncai.com with DigitalOcean hosting

---

## 📋 **PHASE 1: PRE-MIGRATION PREPARATION**

### ✅ **1.1 Docker Audit Results**
**ISSUES FOUND:**
- SSL environment variables causing conflicts:
  ```
  SSL_ENABLED=true
  SSL_CERT_FILE=/etc/ssl/certs/server.crt
  SSL_KEY_FILE=/etc/ssl/private/server.key
  SSL_CA_FILE=/etc/ssl/certs/ca.crt
  ```
- Mixed HTTP/HTTPS configuration
- API container infinite restart loop
- Multiple redundant Docker files

### 🔧 **1.2 Immediate Fixes Needed**
- [ ] Remove SSL configurations from docker-compose.production.yml
- [ ] Create clean production docker-compose.yml
- [ ] Fix container restart loop
- [ ] Remove redundant Docker files

---

## 🌊 **PHASE 2: DIGITALOCEAN SETUP**

### 💰 **2.1 DigitalOcean Droplet Configuration**
**Recommended Specs:**
- **Droplet**: Basic Droplet - $6/month
- **OS**: Ubuntu 22.04 LTS
- **RAM**: 2GB (sufficient for Docker containers)
- **Storage**: 50GB SSD
- **Region**: Choose closest to your location

### 🔐 **2.2 Security Setup**
```bash
# Initial server setup
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 🌐 **PHASE 3: DOMAIN & SSL CONFIGURATION**

### 📍 **3.1 Squarespace DNS Configuration**
**DNS Records to Add:**
```
Type: A
Name: @
Value: [DigitalOcean Droplet IP]
TTL: 300

Type: A  
Name: www
Value: [DigitalOcean Droplet IP]
TTL: 300

Type: CNAME
Name: api
Value: www.flipsyncai.com
TTL: 300
```

### 🔒 **3.2 SSL Certificate Setup (Let's Encrypt)**
```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Generate SSL certificates
sudo certbot --nginx -d flipsyncai.com -d www.flipsyncai.com -d api.flipsyncai.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🚀 **PHASE 4: PRODUCTION DEPLOYMENT**

### 📦 **4.1 Clean Docker Configuration**
**New docker-compose.production.yml:**
```yaml
version: "3.8"

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - api
    restart: unless-stopped

  api:
    build:
      context: .
      dockerfile: Dockerfile.production
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/flipsync
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CORS_ORIGINS=https://www.flipsyncai.com,https://flipsyncai.com
      - EBAY_REDIRECT_URI=https://www.flipsyncai.com/ebay-oauth
      # NO SSL ENVIRONMENT VARIABLES
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=flipsync
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 🌐 **4.2 Nginx Configuration**
```nginx
server {
    listen 80;
    server_name flipsyncai.com www.flipsyncai.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.flipsyncai.com;
    
    ssl_certificate /etc/letsencrypt/live/www.flipsyncai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.flipsyncai.com/privkey.pem;
    
    # Frontend
    location / {
        proxy_pass http://api:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API
    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # CORS headers
        add_header Access-Control-Allow-Origin https://www.flipsyncai.com;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
}
```

---

## 🤖 **PHASE 5: MCP/PLAYWRIGHT SETUP**

### 🐳 **5.1 Playwright Docker Container**
```dockerfile
FROM mcr.microsoft.com/playwright:v1.40.0-focal

WORKDIR /app

# Install MCP server dependencies
RUN npm install -g @modelcontextprotocol/server-playwright

# Copy test scripts
COPY tests/ ./tests/

EXPOSE 3001

CMD ["mcp-server-playwright", "--port", "3001"]
```

### 🔧 **5.2 MCP Gateway Configuration**
```bash
# Install MCP Gateway
docker run -d \
  --name mcp-gateway \
  -p 3001:3001 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  mcp-gateway:latest
```

---

## ✅ **DEPLOYMENT CHECKLIST**

### **Pre-Deployment:**
- [ ] DigitalOcean droplet created
- [ ] DNS records configured in Squarespace
- [ ] SSL certificates generated
- [ ] Clean Docker files prepared

### **Deployment:**
- [ ] Code deployed to DigitalOcean
- [ ] Docker containers started
- [ ] SSL certificates working
- [ ] Domain resolving correctly

### **Post-Deployment:**
- [ ] eBay OAuth flow tested
- [ ] CORS issues resolved
- [ ] All 438 eBay listings accessible
- [ ] MCP/Playwright integration working

---

## 🎯 **EXPECTED RESULTS**

### **Problems Solved:**
✅ SSL certificate authority validation errors  
✅ CORS "Access-Control-Allow-Origin" issues  
✅ Mixed content HTTP/HTTPS problems  
✅ API container infinite restart loop  
✅ eBay OAuth redirect URI issues  

### **New Capabilities:**
🚀 Production-ready deployment  
🤖 Browser automation with MCP/Playwright  
🔒 Proper SSL certificates  
🌐 Real domain with valid certificates  
📱 Mobile-compatible deployment  

---

## 💡 **NEXT STEPS**

1. **Create DigitalOcean account and droplet**
2. **Configure Squarespace DNS**
3. **Deploy clean Docker configuration**
4. **Test eBay OAuth with real domain**
5. **Set up MCP/Playwright for browser automation**

**Estimated Timeline**: 2-4 hours for complete migration
**Cost**: $6/month for DigitalOcean droplet

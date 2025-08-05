# FlipSync Flutter Frontend Deployment Guide

## 🎯 **Overview**

This guide documents the **single, standardized method** for deploying the FlipSync Flutter frontend to production. All legacy deployment methods have been removed to prevent conflicts.

---

## 🏗️ **Architecture**

### **Current Production Setup**
```
Local Development:
├── mobile/build/web/          # Flutter build output
└── deploy_flutter_frontend.sh # Single deployment script

Production Droplet (174.138.77.110):
├── /opt/flipsync/mobile/build/web/  # Source builds (not served)
├── /opt/flipsync/web/               # Served files (nginx document root)
└── nginx:3000 → /opt/flipsync/web/  # Frontend serving
```

### **Build ID Tracking**
- Each build generates a unique MD5 hash stored in `.last_build_id`
- Local and remote build IDs are compared to verify deployments
- Mismatched IDs indicate deployment needed

---

## 🚀 **Deployment Commands**

### **Full Deployment (Recommended)**
```bash
./deploy_flutter_frontend.sh deploy
```
- Builds Flutter web locally
- Transfers files to droplet
- Verifies deployment
- Shows status

### **Build Only**
```bash
./deploy_flutter_frontend.sh build
```
- Builds Flutter web locally only
- Useful for testing builds before deployment

### **Check Status**
```bash
./deploy_flutter_frontend.sh status
```
- Shows local vs remote build IDs
- Checks frontend accessibility
- No changes made

### **Help**
```bash
./deploy_flutter_frontend.sh help
```

---

## 📋 **Deployment Process**

### **Step 1: Pre-deployment Checks**
- ✅ SSH connectivity to droplet
- ✅ Flutter environment setup
- ✅ Mobile directory exists

### **Step 2: Local Build**
- 🧹 Clean previous builds (`flutter clean`)
- 📦 Get dependencies (`flutter pub get`)
- 🔨 Build for production with optimized settings
- 🔍 Verify critical files exist
- 🆔 Generate unique build ID

### **Step 3: Deployment**
- 💾 Backup current web directory
- 📤 Transfer files via rsync
- 🔍 Verify build IDs match
- 🌐 Test frontend accessibility

### **Step 4: Verification**
- ✅ Build ID verification
- ✅ Frontend accessibility test
- 📊 Status report

---

## ⚙️ **Configuration**

### **Production Build Settings**
```bash
flutter build web \
  --release \
  --tree-shake-icons \
  --dart-define=ENVIRONMENT=production \
  --dart-define=API_BASE_URL=http://174.138.77.110:8000/api/v1 \
  --dart-define=WEBSOCKET_URL=ws://174.138.77.110:8000/ws/flipsync \
  --dart-define=BASE_URL=http://174.138.77.110:8000 \
  --dart-define=EBAY_CALLBACK_URL=https://www.flipsyncai.com/api/v1/marketplace/ebay/oauth/callback \
  --dart-define=EBAY_OAUTH_ENABLED=true \
  --dart-define=SSL_ENABLED=false \
  --dart-define=HTTPS_REDIRECT=false \
  --dart-define=ENABLE_ANALYTICS=true \
  --dart-define=DEBUG_MODE=false \
  --dart-define=CACHE_ENABLED=true \
  --dart-define=API_TIMEOUT=30000 \
  --base-href="/" \
  --build-name="1.0.0" \
  --build-number=1
```

### **nginx Configuration**
- **Port**: 3000
- **Document Root**: `/opt/flipsync/web/`
- **SPA Routing**: Enabled (`try_files $uri $uri/ /index.html`)
- **API Proxy**: `/api/` → `localhost:8000`
- **WebSocket Proxy**: `/ws/` → `localhost:8000`

---

## 🔧 **Troubleshooting**

### **Build ID Mismatch**
```bash
# Check status
./deploy_flutter_frontend.sh status

# If IDs don't match, deploy
./deploy_flutter_frontend.sh deploy
```

### **Frontend Not Accessible**
```bash
# Check nginx status on droplet
ssh root@174.138.77.110 "systemctl status nginx"

# Check if files exist
ssh root@174.138.77.110 "ls -la /opt/flipsync/web/"

# Manual test
curl http://174.138.77.110:3000
```

### **Build Failures**
```bash
# Clean and retry
cd mobile
flutter clean
flutter pub get
cd ..
./deploy_flutter_frontend.sh build
```

### **SSH Issues**
```bash
# Test SSH connectivity
ssh root@174.138.77.110 "echo 'Connection test'"
```

---

## 📊 **Monitoring**

### **Access URLs**
- **Frontend**: http://174.138.77.110:3000
- **Backend API**: http://174.138.77.110:8000
- **Health Check**: http://174.138.77.110:8000/health

### **Log Locations**
- **nginx Access**: `/var/log/nginx/access.log`
- **nginx Error**: `/var/log/nginx/error.log`
- **Backend**: `/opt/flipsync/backend.log`

---

## 🚫 **Removed Legacy Methods**

The following deployment methods have been **removed** to prevent conflicts:

### **Removed Files**
- ❌ `flutter_build_output/` (legacy build directory)
- ❌ `flutter_nginx.conf` (conflicting nginx config)
- ❌ `Dockerfile.flutter` (unused Docker config)
- ❌ `docker-compose.production.clean.yml` (unused Docker compose)
- ❌ `mobile/serve_flutter_web.py` (conflicting server script)
- ❌ `fs_agt_clean/deployment/production_deployment_system.py` (conflicting deployment)

### **Deprecated Commands**
- ❌ `python3 -m http.server 3000 --directory build/web`
- ❌ `docker compose up flutter-web`
- ❌ Manual file copying to `/var/www/`

---

## ✅ **Best Practices**

1. **Always use the deployment script** - Never manually copy files
2. **Check status before deploying** - Verify if deployment is needed
3. **Monitor build IDs** - Ensure local and remote match after deployment
4. **Test after deployment** - Verify frontend accessibility
5. **Keep backups** - Script automatically creates backups before deployment

---

## 🔄 **Future Updates**

To update the Flutter frontend:

1. Make changes to Flutter code
2. Run: `./deploy_flutter_frontend.sh deploy`
3. Verify: `./deploy_flutter_frontend.sh status`
4. Test: Visit http://174.138.77.110:3000

**That's it!** No manual steps, no conflicting methods, no confusion.

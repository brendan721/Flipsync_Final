# V3 Backend Endpoints Deployment Guide

## 📋 Overview

This guide provides instructions for deploying the V3 backend endpoints to the production server at `174.138.77.110:8000`.

## ✅ Phase 2 Implementation Status

### **COMPLETED:**
- ✅ V3 User Profile Routes (`v3_user_profile_routes.py`) - **READY FOR DEPLOYMENT**
- ✅ V3 Opportunities Routes (`v3_opportunities_routes.py`) - **READY FOR DEPLOYMENT**  
- ✅ V3 Optimization Routes (`v3_optimization_routes.py`) - **READY FOR DEPLOYMENT**
- ✅ V3 Shipping Zone Endpoints (added to `shipping.py`) - **READY FOR DEPLOYMENT**
- ✅ Main App Integration (`main.py`) - **READY FOR DEPLOYMENT**

### **DEPLOYMENT NEEDED:**
- 🔄 Production backend restart to load new V3 routes

## 🚀 Deployment Instructions

### **Step 1: Verify Files Are Ready**

All required files are present and tested:

```bash
# Verify V3 route files exist
ls -la fs_agt_clean/api/routes/v3_*
# Should show:
# - v3_user_profile_routes.py
# - v3_opportunities_routes.py  
# - v3_optimization_routes.py

# Verify main app integration
grep -n "v3_.*_router" fs_agt_clean/app/main.py
# Should show V3 router imports and includes
```

### **Step 2: Deploy to Production Server**

**Option A: If you have SSH access to 174.138.77.110:**

```bash
# 1. SSH to production server
ssh user@174.138.77.110

# 2. Navigate to application directory
cd /path/to/flipsync/backend

# 3. Pull latest changes (if using git)
git pull origin main

# 4. Restart the backend service
# Find the current uvicorn process
ps aux | grep uvicorn

# Kill the existing process (replace PID with actual process ID)
kill <PID>

# Start the backend with V3 routes
uvicorn fs_agt_clean.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Option B: If using Docker:**

```bash
# 1. Rebuild the Docker container with new V3 routes
docker build -t flipsync-backend .

# 2. Stop the current container
docker stop flipsync-backend-container

# 3. Start new container with V3 routes
docker run -d --name flipsync-backend-container -p 8000:8000 flipsync-backend
```

**Option C: If using systemd service:**

```bash
# 1. Restart the systemd service
sudo systemctl restart flipsync-backend

# 2. Check service status
sudo systemctl status flipsync-backend

# 3. Check logs
sudo journalctl -u flipsync-backend -f
```

### **Step 3: Verify Deployment**

After restarting the backend, run the deployment test:

```bash
# Run the V3 endpoints deployment test
python3 test_v3_endpoints_deployment.py
```

**Expected Results After Successful Deployment:**
- ⚠️ All endpoints should return `401 Unauthorized` (requires authentication)
- ❌ No endpoints should return `404 Not Found`

### **Step 4: Test with Authentication**

Once deployed, test the endpoints with proper JWT authentication:

```bash
# Example authenticated request
curl -H "Authorization: Bearer <JWT_TOKEN>" \
     http://174.138.77.110:8000/api/v1/users/profile
```

## 📊 V3 Endpoints Reference

### **User Profile Endpoints**
- `GET /api/v1/users/profile` - Get user profile with inventory source preferences
- `PUT /api/v1/users/profile` - Update user profile
- `GET /api/v1/users/preferences` - Get user preferences
- `POST /api/v1/users/preferences` - Set user preferences

### **Opportunities Endpoints**
- `GET /api/v1/opportunities/trending/{source}` - Get trending opportunities by source
- `GET /api/v1/opportunities/liquidation` - Get liquidation-specific opportunities
- `GET /api/v1/opportunities/thrifting` - Get thrifting-specific opportunities
- `GET /api/v1/opportunities/miscellaneous` - Get general opportunities
- `POST /api/v1/opportunities/alert` - Set opportunity alert

### **Optimization Endpoints**
- `GET /api/v1/optimization/score/{user_id}` - Get AI-Powered Optimization Score
- `GET /api/v1/optimization/opportunities/{user_id}` - Get optimization opportunities
- `POST /api/v1/optimization/feedback` - Submit optimization feedback

### **Shipping Zone Endpoints**
- `GET /api/v1/shipping/zones/{seller_zip}` - Get USPS shipping zones
- `POST /api/v1/shipping/shippo/poly` - Calculate dimensional shipping
- `GET /api/v1/shipping/savings/{item_id}` - Calculate shipping savings

## 🧪 Testing After Deployment

### **Test 1: Basic Endpoint Availability**
```bash
# Should return 401 (not 404)
curl -s -o /dev/null -w "%{http_code}" http://174.138.77.110:8000/api/v1/users/profile
```

### **Test 2: OpenAPI Documentation**
```bash
# Check if V3 endpoints appear in docs
curl -s http://174.138.77.110:8000/docs | grep -i "v3\|user.*profile\|opportunities\|optimization"
```

### **Test 3: Comprehensive Test Suite**
```bash
# Run full deployment test
python3 test_v3_endpoints_deployment.py

# Expected output after successful deployment:
# ⚠️ Needs Auth: 10/10 endpoints (all require authentication)
# ❌ Not Deployed: 0/10 endpoints
```

## 🚨 Troubleshooting

### **Issue: Endpoints Still Return 404**
**Cause:** Backend not restarted or V3 routes not loaded
**Solution:** 
1. Verify main.py includes V3 router imports
2. Check for import errors in backend logs
3. Restart backend service completely

### **Issue: Import Errors on Startup**
**Cause:** Missing dependencies or syntax errors in V3 routes
**Solution:**
1. Check backend startup logs
2. Verify all imports in V3 route files
3. Test route files individually

### **Issue: Authentication Errors**
**Cause:** JWT token issues or auth dependency problems
**Solution:**
1. Verify `get_current_user` dependency is available
2. Check JWT token format and expiration
3. Test with valid authentication token

## ✅ Success Criteria

Phase 2 is complete when:

1. ✅ All 10 V3 endpoints return `401 Unauthorized` (not `404 Not Found`)
2. ✅ V3 endpoints appear in OpenAPI documentation at `/docs`
3. ✅ Backend logs show successful V3 router loading
4. ✅ Test requests with valid JWT tokens return `200 OK` with expected data

## 📋 Next Steps After Deployment

Once Phase 2 deployment is complete:

1. **Update Flutter V3 Services** - Modify services to call new V3 endpoints instead of fallbacks
2. **Test End-to-End Workflows** - Verify complete user journeys work with real V3 data
3. **Proceed to Phase 3** - Implement revenue-critical features with V3 backend support

---

**Note:** This deployment guide assumes the production backend has the same file structure as the development environment. Adjust paths and commands as needed for your specific deployment setup.

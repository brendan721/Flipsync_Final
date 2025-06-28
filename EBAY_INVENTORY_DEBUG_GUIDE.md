# eBay Inventory Integration Debug Guide

## 🎯 **Issue Summary**

The FlipSync mobile app shows eBay as "connected" but doesn't display actual inventory items. This guide provides step-by-step debugging to identify and fix the root cause.

## 🔍 **Debugging Steps**

### **Step 1: Run the Debug Script**

```bash
cd /home/brend/Flipsync_Final
python debug_ebay_inventory_connection.py
```

This script will test:
- ✅ Backend authentication
- 🔗 eBay connection status
- 📦 eBay inventory endpoint
- 📋 General inventory endpoint

### **Step 2: Check Backend Logs**

```bash
# Check if backend is running
docker ps | grep flipsync

# View backend logs
docker logs flipsync-api -f --tail=100

# Look for eBay-related errors
docker logs flipsync-api 2>&1 | grep -i ebay
```

### **Step 3: Verify eBay Credentials**

Check the `.env` file for eBay credentials:

```bash
cd /home/brend/Flipsync_Final
grep -E "EBAY|SB_EBAY" .env
```

Required credentials:
- `SB_EBAY_APP_ID` - eBay sandbox app ID
- `SB_EBAY_CERT_ID` - eBay sandbox certificate ID
- `SB_EBAY_DEV_ID` - eBay developer ID
- `EBAY_REFRESH_TOKEN` - eBay OAuth refresh token

### **Step 4: Test eBay API Directly**

```bash
# Test eBay sandbox API directly
python test_ebay_sandbox_api_calls.py
```

### **Step 5: Check Mobile App Logs**

If using Flutter web:
1. Open browser developer tools (F12)
2. Go to Console tab
3. Look for API call errors
4. Check Network tab for failed requests

## 🔧 **Common Issues & Fixes**

### **Issue 1: Authentication Problems**

**Symptoms:**
- 401 Unauthorized errors
- "eBay account not connected" messages

**Fix:**
```bash
# Check if auth token is valid
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8001/api/v1/marketplace/ebay/auth/status
```

### **Issue 2: Wrong API Endpoints**

**Symptoms:**
- 404 Not Found errors
- Empty responses

**Current Fix Applied:**
- ✅ Updated mobile app to call `/api/v1/marketplace/ebay/inventory`
- ✅ Fixed response parsing to handle `ApiResponse` format
- ✅ Added proper error handling and logging

### **Issue 3: Data Format Mismatch**

**Symptoms:**
- Data received but not displayed
- Parsing errors in mobile app

**Fix Applied:**
- ✅ Updated `ProductListing.fromEbayInventory()` to handle eBay API format
- ✅ Added comprehensive logging for debugging
- ✅ Added fallback to mock data for development

### **Issue 4: Empty eBay Inventory**

**Symptoms:**
- API calls succeed but return empty arrays
- No actual inventory items in eBay account

**Check:**
```bash
# Verify eBay sandbox has inventory items
python -c "
import asyncio
from fs_agt_clean.agents.market.ebay_agent import EbayAgent

async def check_inventory():
    agent = EbayAgent()
    result = await agent.get_inventory()
    print(f'Inventory items: {len(result.get(\"inventoryItems\", []))}')
    print(f'Sample: {result}')

asyncio.run(check_inventory())
"
```

## 📱 **Mobile App Changes Made**

### **1. API Client Updates**

**File:** `mobile/lib/core/network/api_client_impl.dart`

- ✅ Added eBay inventory methods
- ✅ Fixed endpoint paths to match backend
- ✅ Added proper response parsing for `ApiResponse` format

### **2. Listing Screen Updates**

**File:** `mobile/lib/features/listings/listing_screen.dart`

- ✅ Replaced mock data with real API calls
- ✅ Added comprehensive error handling
- ✅ Added detailed logging for debugging
- ✅ Added `ProductListing.fromEbayInventory()` factory constructor

### **3. API Service Updates**

**File:** `mobile/lib/core/api/api_service.dart`

- ✅ Added eBay inventory service methods
- ✅ Integrated with existing error handling

## 🧪 **Testing the Fix**

### **1. Start the Backend**

```bash
cd /home/brend/Flipsync_Final
docker-compose up -d
```

### **2. Run Debug Script**

```bash
python debug_ebay_inventory_connection.py
```

### **3. Test Mobile App**

```bash
cd mobile
python3 serve_flutter_web.py
```

Navigate to `http://localhost:3000` and check the inventory screen.

### **4. Check Logs**

Look for these log messages in the mobile app console:
- "Loading eBay inventory from API..."
- "eBay connection status: ..."
- "Successfully loaded X eBay inventory items"

## 🎯 **Expected Results**

After applying the fixes:

1. **Debug Script:** Should show all tests passing
2. **Mobile App:** Should display actual eBay inventory items
3. **Logs:** Should show successful API calls and data parsing
4. **No More Mock Data:** Real eBay inventory should replace mock listings

## 🚨 **If Issues Persist**

### **Check Backend Architecture**

The FlipSync backend has a sophisticated 35+ agent architecture. If inventory still doesn't show:

1. **Verify eBay Agent Status:**
   ```bash
   curl http://localhost:8001/api/v1/agents/ebay_agent/status
   ```

2. **Check Agent Logs:**
   ```bash
   docker logs flipsync-api 2>&1 | grep -i "ebay.*agent"
   ```

3. **Verify Marketplace Repository:**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8001/api/v1/marketplace/status
   ```

### **Contact Points**

If the sophisticated backend architecture needs investigation:
- Check `fs_agt_clean/agents/market/ebay_agent.py`
- Review `fs_agt_clean/api/routes/marketplace/ebay.py`
- Examine `fs_agt_clean/core/marketplace/ebay/api_client.py`

**Remember:** The backend represents a production-ready 35+ agent system. Focus on frontend integration rather than backend modifications.

## 📊 **Success Metrics**

- ✅ Debug script shows all tests passing
- ✅ Mobile app displays real eBay inventory items
- ✅ No 404 or authentication errors
- ✅ Inventory count matches eBay sandbox account
- ✅ Product details (title, SKU, stock) display correctly
- ✅ Shipping savings calculations work

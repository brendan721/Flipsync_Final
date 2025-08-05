# FlipSync Configuration Migration Guide

## Overview

FlipSync has migrated from **5 redundant configuration systems** to a **single unified configuration system** that eliminates hardcoded values and provides secure credential management.

## What Changed

### ❌ **Removed (Redundant Configuration Files)**
- `mobile/assets/config/env.development`
- `mobile/assets/config/env.production`
- `mobile/.env.production.template`
- `mobile/build_production_secure.sh`
- `mobile/build_production_https.sh`

### ✅ **New (Unified Configuration System)**
- `mobile/lib/config/environment_config.dart` - Single source of truth
- `mobile/build_unified.sh` - Single build script for all environments
- `mobile/.env` - Development-only defaults (no production credentials)

## Security Improvements

### Before (Insecure)
```bash
# Hardcoded in multiple files
API_BASE_URL=http://174.138.77.110:8000
EBAY_APP_ID=BrendanB-Nashvill-PRD-7f5c11990-62c1c838
OPENAI_API_KEY=sk-proj-9gvKmcp86W7UPE7u2rBTVPRVXa92XTb_Zt5...
```

### After (Secure)
```dart
// Environment-aware with secure injection
static String get apiBaseUrl {
  const override = String.fromEnvironment('API_BASE_URL');
  if (override.isNotEmpty) return override;
  
  switch (environment) {
    case 'production': return 'https://flipsyncai.com/api/v1';
    case 'staging': return 'https://staging.flipsyncai.com/api/v1';
    default: return 'http://localhost:8000/api/v1';
  }
}
```

## Usage

### Development Build
```bash
./build_unified.sh
# Uses localhost defaults, no credentials required
```

### Production Build
```bash
# Method 1: Environment variables
export EBAY_APP_ID="your_app_id"
export EBAY_DEV_ID="your_dev_id"
export EBAY_CERT_ID="your_cert_id"
export EBAY_RU_NAME="your_ru_name"
export AUTH_SECRET="your_auth_secret"
./build_unified.sh -e production

# Method 2: Skip validation for testing
./build_unified.sh -e production --skip-validation
```

### Staging Build
```bash
./build_unified.sh -e staging
```

## Environment Configuration

| Environment | API URL | WebSocket | SSL | Debug | Analytics |
|-------------|---------|-----------|-----|-------|-----------|
| development | localhost:8000 | ws://localhost | No | Yes | No |
| staging | staging.flipsyncai.com | wss://staging | Yes | Yes | No |
| production | flipsyncai.com | wss://flipsyncai.com | Yes | No | Yes |

## Feature Flags

All V3 revenue features are enabled by default:
- ✅ Enhanced Product Creation
- ✅ Shipping Arbitrage
- ✅ External Advertising
- ✅ Real-time WebSocket

Override with `--dart-define` flags if needed.

## Migration Benefits

### 🎯 **Eliminated Redundancy**
- **Before**: 5+ configuration files with overlapping settings
- **After**: 1 unified configuration system

### 🔐 **Enhanced Security**
- **Before**: Hardcoded credentials in version control
- **After**: Secure credential injection via environment variables

### 🚀 **Simplified Deployment**
- **Before**: Multiple build scripts with hardcoded IPs
- **After**: Single build script with environment-aware defaults

### 📊 **Reduced Maintenance**
- **Before**: Update URLs in 5+ places
- **After**: Update in 1 place with automatic environment detection

## Troubleshooting

### Missing Credentials Error
```
❌ Error: Missing required production credentials:
   - EBAY_APP_ID
   - AUTH_SECRET
```

**Solution**: Set environment variables or use `--skip-validation`

### Backend Connectivity Warning
```
⚠️  Warning: Backend may not be accessible at https://flipsyncai.com
```

**Solution**: Ensure backend is running or use `--skip-validation`

### Build Failures
1. Check Flutter installation: `flutter doctor`
2. Clean dependencies: `flutter clean && flutter pub get`
3. Use verbose mode: `./build_unified.sh -v`

## Advanced Usage

### Custom API URL
```bash
export API_BASE_URL="https://custom.domain.com/api/v1"
./build_unified.sh -e production
```

### Debug Production Build
```bash
./build_unified.sh -e production --dart-define=DEBUG_MODE=true
```

### Disable Features
```bash
./build_unified.sh --dart-define=SHIPPING_ARBITRAGE_ENABLED=false
```

## Configuration Reference

See `mobile/lib/config/environment_config.dart` for all available configuration options and their defaults.

---

**✅ Configuration migration complete!** The FlipSync build system is now unified, secure, and maintainable.

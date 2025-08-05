# Legacy WebSocket Cleanup Report
========================================

**Total Legacy Files Found**: 2

## Deprecated Routes

### fs_agt_clean/api/routes/websocket/enhanced_websocket_routes.py
- **Size**: 695 bytes
- **Dependencies**: None found (safe to remove)

## Unused Clients

### fs_agt_clean/core/websocket/phase4_enhanced_websocket.py
- **Size**: 25312 bytes
- **Dependencies**: None found (safe to remove)

## Recommendations

### Safe to Remove (No Dependencies)
- fs_agt_clean/api/routes/websocket/enhanced_websocket_routes.py
- fs_agt_clean/core/websocket/phase4_enhanced_websocket.py

### Next Steps
1. Review dependencies for files that need migration
2. Update imports to use unified WebSocket system
3. Add deprecation notices to files before removal
4. Remove files that are safe to delete

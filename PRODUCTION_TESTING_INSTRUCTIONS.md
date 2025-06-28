# FlipSync Production eBay Testing Instructions

## IMPORTANT SAFETY NOTICE
This configuration enables PRODUCTION eBay API access. All listings created will be LIVE on eBay.

## Safety Measures Enabled
1. **Mandatory Test Prefix**: All listings automatically include "DO NOT BUY - FlipSync Test Product"
2. **Limited Test Listings**: Maximum 3 test listings at any time
3. **Auto-End Listings**: Test listings automatically end after 48 hours
4. **Manual Approval**: All listings require manual approval before going live
5. **Safety Monitoring**: Automated monitoring script checks for compliance

## Testing Workflow

### Phase 1: Setup (30 minutes)
1. Restart FlipSync backend: `docker-compose restart flipsync-api`
2. Verify production eBay configuration is loaded
3. Test eBay OAuth connection through mobile app
4. Confirm safety measures are active

### Phase 2: Controlled Testing (2-4 hours)
1. Create 1-2 test products using provided templates
2. Test complete workflow: analysis → optimization → listing
3. Verify all listings include "DO NOT BUY" prefix
4. Monitor listing creation and agent responses
5. Test pricing optimization and market analysis

### Phase 3: Validation (1 hour)
1. Verify test listings appear on eBay production
2. Confirm safety measures are working
3. Test auto-end functionality
4. Document all findings and metrics

## Emergency Procedures
- **Stop All Testing**: Run `./ebay_safety_monitor.py --emergency-stop`
- **End All Test Listings**: Access eBay Seller Hub and end manually
- **Revert to Sandbox**: Restore .env.backup file and restart

## Success Criteria
✅ eBay OAuth flow works with production credentials
✅ Test listings created with safety prefixes
✅ Agent system provides real recommendations
✅ Pricing optimization functional
✅ All safety measures operational
✅ No unintended live listings created

## Contact Information
- Developer: developer@flipsync.com
- Emergency: Use eBay Seller Hub to manage listings directly

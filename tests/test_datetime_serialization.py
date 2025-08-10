#!/usr/bin/env python3
"""
Test script to verify datetime serialization fix for eBay OAuth tokens.
"""

import json
from datetime import datetime, timezone, timedelta


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def test_datetime_serialization():
    """Test that datetime objects can be serialized to JSON."""
    
    # Create test credentials with datetime objects (similar to eBay OAuth response)
    test_credentials = {
        "access_token": "test_access_token_12345",
        "refresh_token": "test_refresh_token_67890",
        "token_expires_at": datetime.now(timezone.utc) + timedelta(seconds=7200),
        "scopes": ["https://api.ebay.com/oauth/api_scope"],
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    print("🔍 Testing datetime serialization...")
    print(f"Original credentials: {test_credentials}")
    
    try:
        # Test without custom encoder (should fail)
        print("\n❌ Testing without custom encoder...")
        json.dumps(test_credentials)
        print("ERROR: Should have failed!")
    except TypeError as e:
        print(f"✅ Expected error without custom encoder: {e}")
    
    try:
        # Test with custom encoder (should work)
        print("\n✅ Testing with custom DateTimeEncoder...")
        serialized = json.dumps(test_credentials, cls=DateTimeEncoder)
        print(f"Serialized successfully: {serialized[:100]}...")
        
        # Test deserialization
        deserialized = json.loads(serialized)
        print(f"Deserialized successfully: {deserialized}")
        
        print("\n🎉 DateTime serialization fix works correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error with custom encoder: {e}")
        return False


if __name__ == "__main__":
    success = test_datetime_serialization()
    exit(0 if success else 1)

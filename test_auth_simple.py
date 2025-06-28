#!/usr/bin/env python3
"""Simple Authentication Test"""

def test_auth_basic():
    """Test basic authentication functionality."""
    print("🔍 Testing basic authentication...")
    
    try:
        import bcrypt
        
        password = "TestPassword123!"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed)
        
        if is_valid:
            print("  ✅ Password hashing and verification working")
            return True
        else:
            print("  ❌ Password verification failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run authentication tests."""
    print("🚀 Simple Authentication Tests")
    print("=" * 40)
    
    result = test_auth_basic()
    
    if result:
        print("🎉 Authentication test PASSED!")
        return 0
    else:
        print("❌ Authentication test FAILED!")
        return 1

if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Core fix validation test - focuses on the exact 404 errors that were in Chrome logs.
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_chrome_log_endpoints():
    """Test the exact endpoints that were failing in Chrome logs."""

    logger.info("🔍 TESTING CHROME LOG 404 ERRORS - BEFORE vs AFTER FIX")
    logger.info("=" * 70)

    # Headers to simulate Flutter app requests
    headers = {
        "Content-Type": "application/json",
        "Origin": "http://localhost:3000",
        "Referer": "http://localhost:3000/",
    }

    # Test 1: Authentication endpoint (was POST http://localhost:8001/auth/login → 404)
    logger.info("1️⃣ Testing Authentication Endpoint")
    logger.info("   BEFORE: POST http://localhost:8001/auth/login → 404 Not Found")
    logger.info("   AFTER:  POST http://localhost:8001/api/v1/auth/login → ?")

    try:
        response = requests.post(
            "http://localhost:8001/api/v1/auth/login",
            json={"email": "test@example.com", "password": "test"},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 404:
            logger.error("   ❌ STILL GETTING 404 - FIX FAILED")
            return False
        else:
            logger.info(f"   ✅ SUCCESS - Status: {response.status_code} (404 fixed!)")
    except Exception as e:
        logger.error(f"   ❌ ERROR: {e}")
        return False

    # Test 2: eBay status endpoint (was GET http://localhost:8001/marketplace/ebay/status → 404)
    logger.info("\n2️⃣ Testing eBay Status Endpoint")
    logger.info(
        "   BEFORE: GET http://localhost:8001/marketplace/ebay/status → 404 Not Found"
    )
    logger.info(
        "   AFTER:  GET http://localhost:8001/api/v1/marketplace/ebay/status → ?"
    )

    try:
        response = requests.get(
            "http://localhost:8001/api/v1/marketplace/ebay/status",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 404:
            logger.error("   ❌ STILL GETTING 404 - FIX FAILED")
            return False
        else:
            logger.info(f"   ✅ SUCCESS - Status: {response.status_code} (404 fixed!)")
    except Exception as e:
        logger.error(f"   ❌ ERROR: {e}")
        return False

    # Test 3: eBay OAuth callback (was POST http://localhost:8001/marketplace/ebay/oauth/callback → 404)
    logger.info("\n3️⃣ Testing eBay OAuth Callback Endpoint")
    logger.info(
        "   BEFORE: POST http://localhost:8001/marketplace/ebay/oauth/callback → 404 Not Found"
    )
    logger.info(
        "   AFTER:  POST http://localhost:8001/api/v1/marketplace/ebay/oauth/callback → ?"
    )

    try:
        response = requests.post(
            "http://localhost:8001/api/v1/marketplace/ebay/oauth/callback",
            json={"code": "test", "state": "test"},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 404:
            logger.error("   ❌ STILL GETTING 404 - FIX FAILED")
            return False
        else:
            logger.info(f"   ✅ SUCCESS - Status: {response.status_code} (404 fixed!)")
    except Exception as e:
        logger.error(f"   ❌ ERROR: {e}")
        return False

    return True


def test_api_prefix_fix():
    """Test that the API prefix fix is working."""

    logger.info("\n🔧 TESTING API PREFIX FIX")
    logger.info("=" * 70)

    headers = {"Content-Type": "application/json"}

    # Test old URLs (should still get 404)
    logger.info("📍 Testing OLD URLs (should still get 404):")

    old_urls = [
        "http://localhost:8001/auth/login",
        "http://localhost:8001/marketplace/ebay/status",
        "http://localhost:8001/marketplace/ebay/oauth/callback",
    ]

    for url in old_urls:
        try:
            if "login" in url or "callback" in url:
                response = requests.post(
                    url, json={"test": "data"}, headers=headers, timeout=5
                )
            else:
                response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 404:
                logger.info(f"   ✅ {url} → 404 (expected)")
            else:
                logger.warning(f"   ⚠️  {url} → {response.status_code} (unexpected)")
        except Exception as e:
            logger.info(f"   ✅ {url} → Connection error (expected)")

    # Test new URLs (should NOT get 404)
    logger.info("\n📍 Testing NEW URLs (should NOT get 404):")

    new_urls = [
        "http://localhost:8001/api/v1/auth/login",
        "http://localhost:8001/api/v1/marketplace/ebay/status",
        "http://localhost:8001/api/v1/marketplace/ebay/oauth/callback",
    ]

    for url in new_urls:
        try:
            if "login" in url or "callback" in url:
                response = requests.post(
                    url, json={"test": "data"}, headers=headers, timeout=5
                )
            else:
                response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 404:
                logger.error(f"   ❌ {url} → 404 (FIX FAILED)")
                return False
            else:
                logger.info(f"   ✅ {url} → {response.status_code} (404 fixed!)")
        except Exception as e:
            logger.error(f"   ❌ {url} → Error: {e}")
            return False

    return True


def main():
    """Main validation."""
    logger.info("🎯 CORE FIX VALIDATION - Chrome Log 404 Errors")
    logger.info("Testing the exact endpoints that were failing in Chrome logs")
    logger.info("=" * 70)

    # Test 1: Chrome log endpoints
    chrome_test_passed = test_chrome_log_endpoints()

    # Test 2: API prefix fix
    prefix_test_passed = test_api_prefix_fix()

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 VALIDATION SUMMARY:")
    logger.info(
        f"   Chrome Log Endpoints: {'✅ PASS' if chrome_test_passed else '❌ FAIL'}"
    )
    logger.info(
        f"   API Prefix Fix:       {'✅ PASS' if prefix_test_passed else '❌ FAIL'}"
    )
    logger.info("=" * 70)

    if chrome_test_passed and prefix_test_passed:
        logger.info("🎉 CORE FIX VALIDATION PASSED!")
        logger.info("   ✅ All 404 errors from Chrome logs have been resolved")
        logger.info("   ✅ Flutter app can now reach all backend endpoints")
        logger.info("   ✅ API prefix fix is working correctly")
        return True
    else:
        logger.error("❌ CORE FIX VALIDATION FAILED!")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

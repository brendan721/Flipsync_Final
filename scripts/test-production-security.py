#!/usr/bin/env python3
"""
FlipSync Production Security Testing Script
Comprehensive security validation for production deployment
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fs_agt_clean.core.security.vulnerability_scanner import run_security_scan, generate_security_report
from fs_agt_clean.core.security.production_hardening import SecurityConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityTestSuite:
    """Comprehensive security test suite for FlipSync."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "target": base_url,
            "tests": {},
            "overall_status": "UNKNOWN",
            "security_score": 0,
            "critical_issues": 0,
            "recommendations": []
        }
    
    async def run_all_tests(self):
        """Run all security tests."""
        logger.info("🔒 Starting FlipSync Production Security Testing")
        logger.info("=" * 60)
        
        # Test 1: Security Configuration Validation
        await self.test_security_configuration()
        
        # Test 2: Vulnerability Scanning
        await self.test_vulnerability_scan()
        
        # Test 3: Authentication Security
        await self.test_authentication_security()
        
        # Test 4: API Security
        await self.test_api_security()
        
        # Test 5: Rate Limiting
        await self.test_rate_limiting()
        
        # Test 6: Input Validation
        await self.test_input_validation()
        
        # Test 7: Security Headers
        await self.test_security_headers()
        
        # Generate final report
        await self.generate_final_report()
    
    async def test_security_configuration(self):
        """Test security configuration."""
        logger.info("1. Testing Security Configuration...")
        
        try:
            config = SecurityConfig()
            
            # Validate configuration
            issues = []
            
            if not config.force_https:
                issues.append("HTTPS enforcement disabled")
            
            if config.rate_limit_requests_per_minute < 100:
                issues.append("Rate limiting too restrictive for production")
            
            if not config.enable_security_logging:
                issues.append("Security logging disabled")
            
            self.results["tests"]["security_configuration"] = {
                "status": "PASS" if not issues else "FAIL",
                "issues": issues,
                "config": config.dict()
            }
            
            if issues:
                logger.warning(f"   ❌ Configuration issues found: {len(issues)}")
                for issue in issues:
                    logger.warning(f"      - {issue}")
            else:
                logger.info("   ✅ Security configuration validated")
        
        except Exception as e:
            logger.error(f"   ❌ Security configuration test failed: {e}")
            self.results["tests"]["security_configuration"] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def test_vulnerability_scan(self):
        """Run comprehensive vulnerability scan."""
        logger.info("2. Running Vulnerability Scan...")
        
        try:
            # Run the vulnerability scanner
            report = await run_security_scan(self.base_url)
            
            # Store results
            self.results["tests"]["vulnerability_scan"] = {
                "status": "PASS" if report.critical_issues == 0 else "FAIL",
                "security_score": report.overall_score,
                "vulnerabilities_found": report.vulnerabilities_found,
                "critical_issues": report.critical_issues,
                "high_issues": report.high_issues,
                "medium_issues": report.medium_issues,
                "low_issues": report.low_issues,
                "vulnerabilities": report.vulnerabilities,
                "recommendations": report.recommendations
            }
            
            # Update overall results
            self.results["security_score"] = report.overall_score
            self.results["critical_issues"] = report.critical_issues
            self.results["recommendations"].extend(report.recommendations)
            
            logger.info(f"   📊 Security Score: {report.overall_score}/100")
            logger.info(f"   🔍 Vulnerabilities: {report.vulnerabilities_found} total")
            logger.info(f"   🚨 Critical: {report.critical_issues}, High: {report.high_issues}")
            
            if report.critical_issues > 0:
                logger.error("   ❌ Critical vulnerabilities found!")
                for vuln in report.vulnerabilities:
                    if vuln['severity'] == 'CRITICAL':
                        logger.error(f"      - {vuln['title']}: {vuln['description']}")
            else:
                logger.info("   ✅ No critical vulnerabilities found")
        
        except Exception as e:
            logger.error(f"   ❌ Vulnerability scan failed: {e}")
            self.results["tests"]["vulnerability_scan"] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def test_authentication_security(self):
        """Test authentication security."""
        logger.info("3. Testing Authentication Security...")
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Test 1: Authentication endpoint exists
                auth_url = f"{self.base_url}/api/v1/auth/login"
                async with session.post(auth_url, json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }) as response:
                    auth_endpoint_exists = response.status in [400, 401, 422]
                
                # Test 2: JWT token validation
                if auth_endpoint_exists:
                    # Try with valid credentials
                    async with session.post(auth_url, json={
                        "email": "test@example.com",
                        "password": "SecurePassword!"
                    }) as response:
                        if response.status == 200:
                            data = await response.json()
                            jwt_token_returned = "access_token" in data
                        else:
                            jwt_token_returned = False
                else:
                    jwt_token_returned = False
                
                # Test 3: Protected endpoint security
                protected_url = f"{self.base_url}/api/v1/inventory"
                async with session.get(protected_url) as response:
                    requires_auth = response.status == 401
                
                issues = []
                if not auth_endpoint_exists:
                    issues.append("Authentication endpoint not accessible")
                if not requires_auth:
                    issues.append("Protected endpoints don't require authentication")
                
                self.results["tests"]["authentication_security"] = {
                    "status": "PASS" if not issues else "FAIL",
                    "auth_endpoint_exists": auth_endpoint_exists,
                    "jwt_token_returned": jwt_token_returned,
                    "requires_auth": requires_auth,
                    "issues": issues
                }
                
                if issues:
                    logger.warning(f"   ❌ Authentication issues: {len(issues)}")
                    for issue in issues:
                        logger.warning(f"      - {issue}")
                else:
                    logger.info("   ✅ Authentication security validated")
        
        except Exception as e:
            logger.error(f"   ❌ Authentication security test failed: {e}")
            self.results["tests"]["authentication_security"] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def test_api_security(self):
        """Test API security measures."""
        logger.info("4. Testing API Security...")
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Test API versioning
                async with session.get(f"{self.base_url}/api/v1/health") as response:
                    api_versioned = response.status == 200
                
                # Test CORS configuration
                headers = {'Origin': 'https://evil.com'}
                async with session.options(f"{self.base_url}/api/v1/health", headers=headers) as response:
                    cors_origin = response.headers.get('Access-Control-Allow-Origin', '')
                    cors_secure = cors_origin != '*' and 'evil.com' not in cors_origin
                
                # Test content type validation
                async with session.post(f"{self.base_url}/api/v1/inventory", 
                                      data="invalid data", 
                                      headers={'Content-Type': 'text/plain'}) as response:
                    content_type_validated = response.status in [400, 415, 422]
                
                issues = []
                if not api_versioned:
                    issues.append("API versioning not implemented")
                if not cors_secure:
                    issues.append("CORS configuration too permissive")
                if not content_type_validated:
                    issues.append("Content type validation insufficient")
                
                self.results["tests"]["api_security"] = {
                    "status": "PASS" if not issues else "FAIL",
                    "api_versioned": api_versioned,
                    "cors_secure": cors_secure,
                    "content_type_validated": content_type_validated,
                    "issues": issues
                }
                
                if issues:
                    logger.warning(f"   ❌ API security issues: {len(issues)}")
                    for issue in issues:
                        logger.warning(f"      - {issue}")
                else:
                    logger.info("   ✅ API security validated")
        
        except Exception as e:
            logger.error(f"   ❌ API security test failed: {e}")
            self.results["tests"]["api_security"] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def test_rate_limiting(self):
        """Test rate limiting implementation."""
        logger.info("5. Testing Rate Limiting...")
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Send rapid requests to test rate limiting
                url = f"{self.base_url}/api/v1/health"
                tasks = [session.get(url) for _ in range(15)]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for rate limiting
                rate_limited = any(
                    hasattr(r, 'status') and r.status == 429 
                    for r in responses if not isinstance(r, Exception)
                )
                
                # Test authentication rate limiting
                auth_url = f"{self.base_url}/api/v1/auth/login"
                auth_tasks = [
                    session.post(auth_url, json={"email": f"test{i}@example.com", "password": "wrong"})
                    for i in range(10)
                ]
                auth_responses = await asyncio.gather(*auth_tasks, return_exceptions=True)
                
                auth_rate_limited = any(
                    hasattr(r, 'status') and r.status == 429 
                    for r in auth_responses if not isinstance(r, Exception)
                )
                
                issues = []
                if not rate_limited:
                    issues.append("General rate limiting not working")
                if not auth_rate_limited:
                    issues.append("Authentication rate limiting not working")
                
                self.results["tests"]["rate_limiting"] = {
                    "status": "PASS" if not issues else "FAIL",
                    "general_rate_limited": rate_limited,
                    "auth_rate_limited": auth_rate_limited,
                    "issues": issues
                }
                
                if issues:
                    logger.warning(f"   ❌ Rate limiting issues: {len(issues)}")
                    for issue in issues:
                        logger.warning(f"      - {issue}")
                else:
                    logger.info("   ✅ Rate limiting validated")
        
        except Exception as e:
            logger.error(f"   ❌ Rate limiting test failed: {e}")
            self.results["tests"]["rate_limiting"] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def test_input_validation(self):
        """Test input validation."""
        logger.info("6. Testing Input Validation...")
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Test XSS payload
                xss_payload = "<script>alert('xss')</script>"
                async with session.post(f"{self.base_url}/api/v1/inventory", json={
                    "name": xss_payload,
                    "description": xss_payload
                }) as response:
                    xss_blocked = response.status in [400, 422]
                
                # Test SQL injection payload
                sql_payload = "'; DROP TABLE users; --"
                async with session.post(f"{self.base_url}/api/v1/inventory", json={
                    "name": sql_payload
                }) as response:
                    sql_blocked = response.status in [400, 422]
                
                # Test oversized payload
                large_payload = "A" * 100000  # 100KB
                async with session.post(f"{self.base_url}/api/v1/inventory", json={
                    "name": large_payload
                }) as response:
                    size_limited = response.status in [400, 413, 422]
                
                issues = []
                if not xss_blocked:
                    issues.append("XSS payload not blocked")
                if not sql_blocked:
                    issues.append("SQL injection payload not blocked")
                if not size_limited:
                    issues.append("Large payload not rejected")
                
                self.results["tests"]["input_validation"] = {
                    "status": "PASS" if not issues else "FAIL",
                    "xss_blocked": xss_blocked,
                    "sql_blocked": sql_blocked,
                    "size_limited": size_limited,
                    "issues": issues
                }
                
                if issues:
                    logger.warning(f"   ❌ Input validation issues: {len(issues)}")
                    for issue in issues:
                        logger.warning(f"      - {issue}")
                else:
                    logger.info("   ✅ Input validation working")
        
        except Exception as e:
            logger.error(f"   ❌ Input validation test failed: {e}")
            self.results["tests"]["input_validation"] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def test_security_headers(self):
        """Test security headers."""
        logger.info("7. Testing Security Headers...")
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    headers = response.headers
                    
                    # Required security headers
                    required_headers = [
                        'X-Content-Type-Options',
                        'X-Frame-Options',
                        'X-XSS-Protection',
                        'Referrer-Policy'
                    ]
                    
                    missing_headers = [h for h in required_headers if h not in headers]
                    
                    # Check for information disclosure
                    server_header = headers.get('Server', '')
                    info_disclosed = any(tech in server_header.lower() for tech in ['apache', 'nginx', 'iis', 'python', 'fastapi'])
                    
                    issues = []
                    if missing_headers:
                        issues.extend([f"Missing header: {h}" for h in missing_headers])
                    if info_disclosed:
                        issues.append("Server information disclosed")
                    
                    self.results["tests"]["security_headers"] = {
                        "status": "PASS" if not issues else "FAIL",
                        "headers_present": {h: h in headers for h in required_headers},
                        "server_header": server_header,
                        "info_disclosed": info_disclosed,
                        "issues": issues
                    }
                    
                    if issues:
                        logger.warning(f"   ❌ Security header issues: {len(issues)}")
                        for issue in issues:
                            logger.warning(f"      - {issue}")
                    else:
                        logger.info("   ✅ Security headers validated")
        
        except Exception as e:
            logger.error(f"   ❌ Security headers test failed: {e}")
            self.results["tests"]["security_headers"] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    async def generate_final_report(self):
        """Generate final security report."""
        logger.info("8. Generating Final Security Report...")
        
        # Calculate overall status
        test_statuses = [test.get("status", "ERROR") for test in self.results["tests"].values()]
        failed_tests = [status for status in test_statuses if status in ["FAIL", "ERROR"]]
        
        if not failed_tests:
            self.results["overall_status"] = "PASS"
        elif len(failed_tests) <= 2 and self.results["critical_issues"] == 0:
            self.results["overall_status"] = "PASS_WITH_WARNINGS"
        else:
            self.results["overall_status"] = "FAIL"
        
        # Save detailed report
        report_file = f"security_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        logger.info("=" * 60)
        logger.info("🔒 FLIPSYNC PRODUCTION SECURITY REPORT")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {self.results['overall_status']}")
        logger.info(f"Security Score: {self.results['security_score']}/100")
        logger.info(f"Critical Issues: {self.results['critical_issues']}")
        logger.info(f"Tests Passed: {test_statuses.count('PASS')}/{len(test_statuses)}")
        logger.info(f"Detailed Report: {report_file}")
        
        if self.results["overall_status"] == "PASS":
            logger.info("✅ FlipSync is ready for production deployment!")
        elif self.results["overall_status"] == "PASS_WITH_WARNINGS":
            logger.warning("⚠️  FlipSync has minor security issues but is acceptable for production")
        else:
            logger.error("❌ FlipSync has critical security issues - DO NOT deploy to production!")
        
        return self.results


async def main():
    """Main function to run security tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FlipSync Production Security Testing")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL to test")
    args = parser.parse_args()
    
    suite = SecurityTestSuite(args.url)
    results = await suite.run_all_tests()
    
    # Exit with appropriate code
    if results["overall_status"] == "FAIL":
        sys.exit(1)
    elif results["overall_status"] == "PASS_WITH_WARNINGS":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

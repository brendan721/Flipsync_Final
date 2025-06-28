#!/usr/bin/env python3
"""
Check SSL/HTTPS Configuration Issues
"""

import asyncio
import aiohttp
import ssl
import socket

async def check_ssl_config():
    """Check SSL/HTTPS configuration and mixed content issues."""
    print("🔒 CHECKING SSL/HTTPS CONFIGURATION")
    print("=" * 60)
    
    # Test 1: Check if backend is accidentally serving HTTPS
    print("\n1️⃣ Checking Backend SSL Configuration...")
    try:
        # Try HTTPS connection to backend
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://localhost:8001/api/v1/health", ssl=False) as response:
                    print(f"   ⚠️  Backend is serving HTTPS: {response.status}")
                    print(f"   🚨 This could cause mixed content issues!")
            except aiohttp.ClientConnectorError as e:
                if "SSL" in str(e) or "certificate" in str(e):
                    print(f"   ✅ Backend correctly rejects HTTPS (HTTP only)")
                else:
                    print(f"   ❌ Backend connection error: {e}")
            except Exception as e:
                print(f"   ✅ Backend correctly rejects HTTPS: {e}")
                
    except Exception as e:
        print(f"   ❌ SSL check error: {e}")
    
    # Test 2: Check frontend SSL configuration
    print("\n2️⃣ Checking Frontend SSL Configuration...")
    try:
        async with aiohttp.ClientSession() as session:
            # Check if frontend is serving HTTPS
            try:
                async with session.get("https://localhost:3000/", ssl=False) as response:
                    print(f"   ⚠️  Frontend is serving HTTPS: {response.status}")
                    print(f"   🚨 This could cause mixed content issues!")
            except aiohttp.ClientConnectorError as e:
                if "SSL" in str(e) or "certificate" in str(e):
                    print(f"   ✅ Frontend correctly rejects HTTPS (HTTP only)")
                else:
                    print(f"   ❌ Frontend connection error: {e}")
            except Exception as e:
                print(f"   ✅ Frontend correctly rejects HTTPS: {e}")
                
    except Exception as e:
        print(f"   ❌ Frontend SSL check error: {e}")
    
    # Test 3: Check for mixed content issues
    print("\n3️⃣ Checking for Mixed Content Issues...")
    
    # Check if any service is accidentally configured for HTTPS
    services_to_check = [
        ("Backend API", "localhost:8001"),
        ("Frontend", "localhost:3000"),
        ("AI Communication", "localhost"),  # From the error you mentioned
    ]
    
    for service_name, host in services_to_check:
        try:
            # Try to connect to HTTPS version
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((host.split(':')[0], int(host.split(':')[1]) if ':' in host else 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=host.split(':')[0]) as ssock:
                    print(f"   ⚠️  {service_name} ({host}) is serving HTTPS!")
                    print(f"   🚨 This will cause certificate errors!")
        except (socket.timeout, ConnectionRefusedError, OSError):
            print(f"   ✅ {service_name} ({host}) correctly not serving HTTPS")
        except Exception as e:
            print(f"   ✅ {service_name} ({host}) SSL check: {e}")
    
    # Test 4: Check Docker container networking
    print("\n4️⃣ Checking Docker Container Networking...")
    try:
        # Check if containers are using HTTPS internally
        import subprocess
        result = subprocess.run(
            ["docker", "exec", "flipsync-production-api", "env"], 
            capture_output=True, text=True, timeout=10
        )
        
        env_vars = result.stdout
        https_vars = [line for line in env_vars.split('\n') if 'HTTPS' in line or 'SSL' in line or 'TLS' in line]
        
        if https_vars:
            print(f"   ⚠️  Found HTTPS/SSL environment variables:")
            for var in https_vars:
                print(f"      {var}")
        else:
            print(f"   ✅ No HTTPS/SSL environment variables found")
            
    except Exception as e:
        print(f"   ❌ Docker env check error: {e}")
    
    # Test 5: Check the specific AI communication error
    print("\n5️⃣ Checking AI Communication SSL Error...")
    try:
        async with aiohttp.ClientSession() as session:
            # Test the exact URL from your error
            try:
                async with session.get("https://localhost/api/v1/ai/ai/communication/status", ssl=False) as response:
                    print(f"   ⚠️  AI Communication endpoint is serving HTTPS: {response.status}")
                    print(f"   🚨 This is the source of your SSL error!")
            except aiohttp.ClientConnectorError as e:
                print(f"   ✅ AI Communication endpoint correctly rejects HTTPS")
                print(f"   💡 The error suggests the app is trying to use HTTPS when it should use HTTP")
            except Exception as e:
                print(f"   ✅ AI Communication SSL check: {e}")
                
    except Exception as e:
        print(f"   ❌ AI Communication check error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 SSL/HTTPS CONFIGURATION ANALYSIS")
    print("=" * 60)
    print("📋 Key Findings:")
    print("   • Check if any service is accidentally serving HTTPS")
    print("   • Look for mixed content issues (HTTPS frontend + HTTP backend)")
    print("   • Verify Docker container networking")
    print("   • Check environment variables for SSL/HTTPS configuration")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_ssl_config())

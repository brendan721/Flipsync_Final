#!/usr/bin/env python3
"""
Use eBay Console OAuth URL
This script helps you use the OAuth URL directly from your eBay developer console
"""

import webbrowser
import urllib.parse

def main():
    print("🔐 eBay Console OAuth URL Helper")
    print("=" * 50)
    print()
    
    print("📋 INSTRUCTIONS:")
    print("1. Go to your eBay developer console")
    print("2. Find the 'Your branded eBay Sandbox Sign In (OAuth)' section")
    print("3. Copy the COMPLETE OAuth URL (click 'See all' if needed)")
    print("4. Paste it below when prompted")
    print()
    
    # Get the OAuth URL from user
    oauth_url = input("🔗 Paste your complete eBay OAuth URL here: ").strip()
    
    if not oauth_url.startswith("https://auth.sandbox.ebay.com/oauth2/authorize"):
        print("❌ Error: This doesn't look like a valid eBay OAuth URL")
        print("   Make sure you copied the complete URL starting with:")
        print("   https://auth.sandbox.ebay.com/oauth2/authorize...")
        return
    
    print()
    print("✅ OAuth URL received!")
    print()
    
    # Parse the URL to extract parameters
    try:
        parsed_url = urllib.parse.urlparse(oauth_url)
        params = urllib.parse.parse_qs(parsed_url.query)
        
        client_id = params.get('client_id', [''])[0]
        redirect_uri = params.get('redirect_uri', [''])[0]
        scopes = params.get('scope', [''])[0]
        
        print("📊 URL Analysis:")
        print(f"   Client ID: {client_id}")
        print(f"   Redirect URI: {redirect_uri}")
        print(f"   Scopes: {len(scopes.split()) if scopes else 0} scopes included")
        print()
        
    except Exception as e:
        print(f"⚠️ Could not parse URL details: {e}")
        print()
    
    # Open the URL
    print("🌐 Opening OAuth URL in your browser...")
    webbrowser.open(oauth_url)
    print()
    
    print("📝 NEXT STEPS:")
    print("1. Complete the OAuth flow in the browser")
    print("2. Sign in with your eBay sandbox account")
    print("3. Grant permissions to your application")
    print("4. After redirect, copy the authorization code from the URL")
    print("5. The code will be in the format: code=v^1.1#i^1#...")
    print()
    
    # Wait for authorization code
    print("⏳ Waiting for you to complete the OAuth flow...")
    auth_code = input("🔑 Paste the authorization code here: ").strip()
    
    if not auth_code:
        print("❌ No authorization code provided")
        return
    
    # URL decode if needed
    if '%' in auth_code:
        auth_code = urllib.parse.unquote(auth_code)
    
    print()
    print("✅ Authorization code received!")
    print(f"   Code preview: {auth_code[:50]}...")
    print()
    
    print("🔄 Now run the token exchange:")
    print(f"   python exchange_oauth_code.py '{auth_code}'")
    print()
    
    # Save the code to a file for easy access
    with open("auth_code.txt", "w") as f:
        f.write(auth_code)
    
    print("💾 Authorization code saved to: auth_code.txt")
    print()
    print("🎯 If the exchange fails, the issue might be:")
    print("   1. Code expired (codes expire in ~5 minutes)")
    print("   2. Redirect URI mismatch in our exchange script")
    print("   3. Client credentials mismatch")

if __name__ == "__main__":
    main()

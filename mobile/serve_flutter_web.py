#!/usr/bin/env python3
"""
Simple HTTP server to serve the Flutter web app for testing
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path


def main():
    # Change to the web build directory
    web_dir = Path(__file__).parent / "build" / "web"

    if not web_dir.exists():
        print("❌ Error: Web build directory not found!")
        print("   Please run 'flutter build web' first")
        sys.exit(1)

    os.chdir(web_dir)

    # Set up the server
    PORT = 3000
    Handler = http.server.SimpleHTTPRequestHandler

    # Add CORS headers for API requests
    class CORSRequestHandler(Handler):
        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            super().end_headers()

    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print("🚀 FlipSync Flutter Web App Server")
        print("=" * 50)
        print(f"📱 Serving Flutter app at: http://localhost:{PORT}")
        print(f"📁 Serving from: {web_dir}")
        print("🔗 Backend API: http://localhost:8001/api/v1")
        print("")
        print("✅ Ready for testing!")
        print("   - Open http://localhost:3000 in your browser")
        print("   - The app will connect to the backend on port 8001")
        print("")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")


if __name__ == "__main__":
    main()

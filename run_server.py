#!/usr/bin/env python3
"""
Simple HTTP Server for Link AI Project
Run this script to serve the HTML files locally
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def main():
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Create server
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 Server started at http://localhost:{PORT}")
        print(f"📁 Serving files from: {project_dir}")
        print(f"🌐 Open your browser and go to: http://localhost:{PORT}")
        print(f"📱 Main page: http://localhost:{PORT}/index.html")
        print(f"💬 Chat page: http://localhost:{PORT}/chat.html")
        print(f"🔐 Sign in: http://localhost:{PORT}/signin.html")
        print(f"📝 Sign up: http://localhost:{PORT}/signup.html")
        print(f"🏠 Welcome: http://localhost:{PORT}/welcome.html")
        print("\nPress Ctrl+C to stop the server")
        
        # Try to open browser automatically
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    main() 
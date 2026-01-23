# WSGI configuration for PythonAnywhere
# Copy this content to: /var/www/ahmedmansour0022_pythonanywhere_com_wsgi.py

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/ahmedmansour0022/video_rag'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

# Import and create the WSGI application
# For FastAPI, we need to use the ASGI-to-WSGI adapter
from app.main import app as fastapi_app

# PythonAnywhere free tier only supports WSGI, not ASGI
# We need to use a WSGI wrapper for FastAPI
# Option 1: Use a2wsgi (recommended)
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(fastapi_app)
except ImportError:
    # Fallback: basic WSGI wrapper (limited functionality)
    import asyncio
    from io import BytesIO
    
    def application(environ, start_response):
        """Basic WSGI wrapper for FastAPI (limited - only for health check)"""
        path = environ.get('PATH_INFO', '/')
        
        if path == '/health':
            status = '200 OK'
            response_headers = [('Content-type', 'application/json')]
            start_response(status, response_headers)
            return [b'{"status": "ok", "message": "Use Streamlit app for full functionality"}']
        
        status = '200 OK'
        response_headers = [('Content-type', 'text/html')]
        start_response(status, response_headers)
        html = b'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Video Repair Assistant API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #1f77b4; }
                .info { background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .warning { background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; }
                code { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>Video Repair Assistant API</h1>
            <div class="info">
                <h3>API Status: Running</h3>
                <p>The FastAPI backend is deployed on PythonAnywhere.</p>
            </div>
            <div class="warning">
                <h3>Note</h3>
                <p>For full functionality (video analysis, voice conversation), please install <code>a2wsgi</code>:</p>
                <pre>pip install a2wsgi</pre>
            </div>
            <h3>Available Endpoints:</h3>
            <ul>
                <li><code>GET /health</code> - Health check</li>
                <li><code>POST /video/analyze</code> - Analyze video</li>
                <li><code>POST /assist/video</code> - Full assistance pipeline</li>
                <li><code>POST /knowledge-base/documents</code> - Upload documents</li>
            </ul>
        </body>
        </html>
        '''
        return [html]

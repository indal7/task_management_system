#!/usr/bin/env python3
"""
Task Management System - Development Entry Point
Run with: python app.py
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from app import create_app
from config import get_config

def main():
    """Main application function for development."""
    # Load environment from environment variable or default
    env = os.getenv('FLASK_ENV', 'development')
    print(f"🔧 Using environment: {env}")
    # Load appropriate environment file
    env_file = f"env/.env.{env}"
    print(f"📂 Loading environment file: {env_file}")
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    
    # Create the Flask application
    config_class = get_config(env)
    app = create_app(config_class)
    
    # Development server configuration
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    # ✅ USE LOGGER INSTEAD OF PRINT STATEMENTS
    app.logger.info(f"🌐 Server starting on: http://{host}:{port}")
    app.logger.info(f"📊 Environment: {env}")
    app.logger.info(f"🔧 Debug Mode: {debug}")
    app.logger.info("=" * 50)

    
    # Run with Socket.IO support if available
    if hasattr(app, 'socketio'):
        app.socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )
    else:
        app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    main()
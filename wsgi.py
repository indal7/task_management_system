"""
WSGI Entry Point for Production Deployment
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Load environment variables
env = os.getenv('FLASK_ENV', 'production')
env_file = f"env/.env.{env}"
if os.path.exists(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)

from app import create_app
from config import get_config

# Create application instance
config_class = get_config(env)
app = create_app(config_class)

# Verify setup
with app.app_context():
    try:
        from app.utils.database import test_connection
        test_connection()
        print(f"✅ WSGI: Application ready in {env} mode")
    except Exception as e:
        print(f"❌ WSGI: Setup error: {e}")

if __name__ == "__main__":
    # For testing WSGI directly
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))
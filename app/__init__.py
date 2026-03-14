"""
Flask Application Factory
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=[])

def create_app(config_class):
    """Create Flask application instance"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Setup logging first (before anything else)
    from app.utils.logger import setup_logging
    setup_logging(app)
    app.logger.info("🚀 Starting Task Management System")

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    app.logger.info("✅ Database extensions initialized")

    # Initialize rate limiter
    if app.config.get('RATELIMIT_ENABLED', True):
        limiter.storage_uri = app.config.get(
            'RATELIMIT_STORAGE_URL', 'memory://'
        )
    else:
        limiter.storage_uri = 'memory://'
    limiter.init_app(app)
    app.logger.info("✅ Rate limiter initialized")

    # Initialize caching
    from app.utils.cache_utils import init_cache
    cache = init_cache(app)
    app.cache = cache
    app.logger.info("✅ Cache extension initialized")
    
    # Configure CORS for the Angular dev server
    CORS(
        app,
        resources={r"/api/*": {"origins": "http://localhost:4200"}},
        supports_credentials=True
    )
    
    # Initialize Socket.IO
    from app.utils.socket_utils import init_socketio
    socketio = init_socketio(app)
    app.socketio = socketio
    app.logger.info("✅ Socket.IO initialized")

    # Import and register models
    from app import models
    
    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)
    app.logger.info("✅ Blueprints registered")

    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            app.logger.debug(f"  {methods:15} {rule.rule}")
    
    # Register error handlers
    register_basic_error_handlers(app)
    
    return app

def register_basic_error_handlers(app):
    """Register basic error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning(f"404 Error: {error}")
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        app.logger.warning(f"Rate limit exceeded: {error}")
        return {'error': 'Too many requests. Please try again later.'}, 429

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"500 Error: {error}", exc_info=True)
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle unexpected exceptions"""
        db.session.rollback()
        app.logger.error(f"Unhandled exception: {e}", exc_info=True)
        if app.config.get('DEBUG'):
            raise e
        return {'error': 'An unexpected error occurred'}, 500


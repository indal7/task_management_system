"""
API routes for Task Management System
"""
import logging
from flask import Flask
from app.routes.auth_routes import auth_bp
from app.routes.task_routes import task_bp
from app.routes.project_routes import project_bp
from app.routes.comment_routes import comment_bp
from app.routes.notification_routes import notification_bp
from app.routes.analytics_routes import analytics_bp
from app.routes.sprint_routes import sprint_bp
from app.routes.enum_routes import enum_bp
from app.routes.cache_routes import cache_bp
from app.routes.user_routes import user_bp
from app.routes.member_routes import member_bp
from app.routes.attachment_routes import attachment_bp
from app.routes.search_routes import search_bp
from app.routes.activity_routes import activity_bp
from app.routes.bulk_routes import bulk_bp

logger = logging.getLogger('app.api')


def register_blueprints(app: Flask):
    """Register all blueprints with the Flask app"""
    blueprints = [
        auth_bp,
        task_bp,
        project_bp,
        sprint_bp,
        comment_bp,
        notification_bp,
        analytics_bp,
        enum_bp,
        cache_bp,
        user_bp,
        member_bp,
        attachment_bp,
        search_bp,
        activity_bp,
        bulk_bp,
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Register health check routes
    register_health_routes(app)

    logger.info("All blueprints registered successfully")


def register_health_routes(app: Flask):
    """Register health check endpoints"""

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'task-management-api'}, 200

    @app.route('/health/db')
    def db_health_check():
        from app.utils.database import test_connection
        try:
            test_connection()
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, 500

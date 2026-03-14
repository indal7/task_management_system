"""
API routes for Task Management System
"""
from flask import Flask
from app.routes.auth_routes import auth_bp
from app.routes.task_routes import task_bp
from app.routes.project_routes import project_bp
from app.routes.comment_routes import comment_bp
from app.routes.notification_routes import notification_bp
from app.routes.analytics_routes import analytics_bp
from app.routes.sprint_routes import sprint_bp
from app.routes.enum_routes import enum_bp

def register_blueprints(app: Flask):
    """Register all blueprints with the Flask app"""
    blueprints = [
        (auth_bp, '/api/auth'),
        (task_bp, '/api/tasks'),
        (project_bp, '/api/projects'),
        (sprint_bp, '/api/sprints'),
        (comment_bp, '/api/comments'),
        (notification_bp, '/api/notifications'),
        (analytics_bp, '/api/analytics'),
        (enum_bp, '/api/enums'),
    ]
    
    for blueprint, prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=prefix)
    
    # Register health check routes
    register_health_routes(app)
    
    print("✅ All blueprints registered successfully")

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
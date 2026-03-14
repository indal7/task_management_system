# app/urls.py
from flask import Flask
from app.routes.auth_routes import auth_bp
from app.routes.task_routes import task_bp
from app.routes.project_routes import project_bp
from app.routes.comment_routes import comment_bp
from app.routes.notification_routes import notification_bp
from app.routes.analytics_routes import analytics_bp
from app.routes.sprint_routes import sprint_bp
from app.routes.enum_routes import enum_bp

def register_routes(app: Flask):
    """Register all route blueprints with the Flask app."""
    
    # Core functionality routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(sprint_bp)
    app.register_blueprint(enum_bp)
    print("✅ Core routes registered successfully!")
    
    
    # Print registered routes for debugging
    print("\n📋 Registered API Routes:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f"  {methods:10} {rule.rule}")
    print()

def get_api_info():
    """Get information about available API endpoints."""
    return {
        "authentication": {
            "prefix": "/api/auth",
            "endpoints": [
                "POST /api/auth/register - Register new user",
                "POST /api/auth/login - User login",
                "POST /api/auth/refresh - Refresh access token",
                "GET /api/auth/profile - Get user profile",
                "PUT /api/auth/profile - Update user profile",
                "POST /api/auth/change-password - Change password",
                "GET /api/auth/users - Get all users (for assignments)"
            ]
        },
        "tasks": {
            "prefix": "/api/tasks",
            "endpoints": [
                "GET /api/tasks - Get tasks with filters",
                "POST /api/tasks - Create new task",
                "GET /api/tasks/overdue - Get overdue tasks",
                "GET /api/tasks/{id} - Get task by ID",
                "PUT /api/tasks/{id} - Update task",
                "DELETE /api/tasks/{id} - Delete task",
                "POST /api/tasks/{id}/assign - Assign task to user",
                "POST /api/tasks/{id}/comments - Add comment to task",
                "POST /api/tasks/{id}/time - Log time on task",
                "GET /api/tasks/{id}/time - Get time logs for task"
            ]
        },
        "projects": {
            "prefix": "/api/projects",
            "endpoints": [
                "GET /api/projects - Get user's projects",
                "POST /api/projects - Create new project",
                "GET /api/projects/{id} - Get project by ID",
                "PUT /api/projects/{id} - Update project",
                "DELETE /api/projects/{id} - Delete project",
                "POST /api/projects/{id}/members - Add team member",
                "DELETE /api/projects/{id}/members/{user_id} - Remove team member",
                "GET /api/projects/{id}/tasks - Get project tasks"
            ]
        },
        "sprints": {
            "prefix": "/api/sprints",
            "endpoints": [
                "POST /api/sprints - Create new sprint",
                "GET /api/sprints/{id} - Get sprint by ID",
                "PUT /api/sprints/{id} - Update sprint",
                "DELETE /api/sprints/{id} - Delete sprint",
                "GET /api/sprints/project/{project_id} - Get project sprints",
                "POST /api/sprints/{id}/start - Start sprint",
                "POST /api/sprints/{id}/complete - Complete sprint",
                "GET /api/sprints/{id}/burndown - Get burndown data",
                "POST /api/sprints/{id}/tasks/{task_id} - Add task to sprint",
                "DELETE /api/sprints/{id}/tasks/{task_id} - Remove task from sprint"
            ]
        },
        "notifications": {
            "prefix": "/api/notifications",
            "endpoints": [
                "GET /api/notifications - Get user notifications",
                "PUT /api/notifications/{id}/read - Mark notification as read",
                "POST /api/notifications/mark-all-read - Mark all as read"
            ]
        },
        "analytics": {
            "prefix": "/api/analytics",
            "endpoints": [
                "GET /api/analytics/dashboard - Get dashboard data",
                "GET /api/analytics/tasks - Get task analytics",
                "GET /api/analytics/projects - Get project analytics",
                "GET /api/analytics/users - Get user analytics"
            ]
        },
        "enums": {
            "prefix": "/api/enums",
            "endpoints": [
                "GET /api/enums - Get all enum values",
                "GET /api/enums/user-roles - Get user roles",
                "GET /api/enums/task-statuses - Get task statuses",
                "GET /api/enums/task-priorities - Get task priorities",
                "GET /api/enums/task-types - Get task types",
                "GET /api/enums/project-statuses - Get project statuses",
                "GET /api/enums/sprint-statuses - Get sprint statuses"
            ]
        }
    }
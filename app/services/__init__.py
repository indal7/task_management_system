"""
Business logic services for Task Management System
"""

from .auth_service import AuthService
from .task_service import TaskService
from .project_service import ProjectService
from .sprint_service import SprintService
from .notification_service import NotificationService
from .analytics_service import AnalyticsService
# from .email_service import EmailService
# from .socket_service import SocketService
# from .socket_service import SocketService, init_socketio  # Import both class and function

__all__ = [
    'AuthService', 'TaskService', 'ProjectService', 'SprintService',
    'NotificationService', 'AnalyticsService'
]
# app/models/enums.py
from enum import Enum

class UserRole(Enum):
    ADMIN = "ADMIN"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    TEAM_LEAD = "TEAM_LEAD"
    SENIOR_DEVELOPER = "SENIOR_DEVELOPER"
    DEVELOPER = "DEVELOPER"
    QA_ENGINEER = "QA_ENGINEER"
    DEVOPS_ENGINEER = "DEVOPS_ENGINEER"
    UI_UX_DESIGNER = "UI_UX_DESIGNER"
    BUSINESS_ANALYST = "BUSINESS_ANALYST"
    PRODUCT_OWNER = "PRODUCT_OWNER"
    SCRUM_MASTER = "SCRUM_MASTER"

class TaskStatus(Enum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    TESTING = "TESTING"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    DEPLOYED = "DEPLOYED"

class TaskPriority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class TaskType(Enum):
    FEATURE = "FEATURE"
    BUG = "BUG"
    ENHANCEMENT = "ENHANCEMENT"
    REFACTOR = "REFACTOR"
    DOCUMENTATION = "DOCUMENTATION"
    TESTING = "TESTING"
    DEPLOYMENT = "DEPLOYMENT"
    RESEARCH = "RESEARCH"
    MAINTENANCE = "MAINTENANCE"
    SECURITY = "SECURITY"

class ProjectStatus(Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class SprintStatus(Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class NotificationType(Enum):
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_UPDATED = "TASK_UPDATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_OVERDUE = "TASK_OVERDUE"
    COMMENT_ADDED = "COMMENT_ADDED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    SPRINT_STARTED = "SPRINT_STARTED"
    SPRINT_COMPLETED = "SPRINT_COMPLETED"
    MENTION = "MENTION"

class EstimationUnit(Enum):
    HOURS = "HOURS"
    DAYS = "DAYS"
    STORY_POINTS = "STORY_POINTS"

# Utility methods for serialization
def enum_to_list(enum_class):
    """Returns a list of enum values."""
    return [e.value for e in enum_class]

def enum_to_dict(enum_class):
    """Returns a dictionary of enum names and values."""
    return {e.name: e.value for e in enum_class}

def format_label(value):
    """Format enum value to readable label."""
    return value.replace('_', ' ').title()

# Enhanced enum configurations
TASK_TYPE_CONFIG = {
    'FEATURE': {'label': 'Feature', 'icon': 'fa-star', 'color': '#28a745', 'default_estimation_unit': 'STORY_POINTS', 'requires_approval': False},
    'BUG': {'label': 'Bug', 'icon': 'fa-bug', 'color': '#dc3545', 'default_estimation_unit': 'HOURS', 'requires_approval': False},
    'ENHANCEMENT': {'label': 'Enhancement', 'icon': 'fa-arrow-up', 'color': '#17a2b8', 'default_estimation_unit': 'STORY_POINTS', 'requires_approval': False},
    'REFACTOR': {'label': 'Refactor', 'icon': 'fa-code', 'color': '#6f42c1', 'default_estimation_unit': 'HOURS', 'requires_approval': False},
    'TESTING': {'label': 'Testing', 'icon': 'fa-check', 'color': '#fd7e14', 'default_estimation_unit': 'HOURS', 'requires_approval': False},
    'DOCUMENTATION': {'label': 'Documentation', 'icon': 'fa-file-text', 'color': '#6c757d', 'default_estimation_unit': 'HOURS', 'requires_approval': False},
    'MAINTENANCE': {'label': 'Maintenance', 'icon': 'fa-wrench', 'color': '#20c997', 'default_estimation_unit': 'HOURS', 'requires_approval': False},
    'SECURITY': {'label': 'Security', 'icon': 'fa-shield', 'color': '#e83e8c', 'default_estimation_unit': 'STORY_POINTS', 'requires_approval': True},
    'DEPLOYMENT': {'label': 'Deployment', 'icon': 'fa-rocket', 'color': '#007bff', 'default_estimation_unit': 'HOURS', 'requires_approval': True},
    'RESEARCH': {'label': 'Research', 'icon': 'fa-search', 'color': '#ffc107', 'default_estimation_unit': 'STORY_POINTS', 'requires_approval': False}
}

TASK_PRIORITY_CONFIG = {
    'CRITICAL': {'label': 'Critical', 'icon': 'fa-exclamation-triangle', 'color': '#dc3545', 'severity_level': 4, 'escalation_hours': 4},
    'HIGH': {'label': 'High', 'icon': 'fa-arrow-up', 'color': '#fd7e14', 'severity_level': 3, 'escalation_hours': 24},
    'MEDIUM': {'label': 'Medium', 'icon': 'fa-minus', 'color': '#ffc107', 'severity_level': 2, 'escalation_hours': 72},
    'LOW': {'label': 'Low', 'icon': 'fa-arrow-down', 'color': '#28a745', 'severity_level': 1, 'escalation_hours': 168}
}

TASK_STATUS_CONFIG = {
    'BACKLOG': {'label': 'Backlog', 'icon': 'fa-inbox', 'color': '#6c757d', 'is_completed': False, 'is_active': False, 'next_statuses': ['TODO']},
    'TODO': {'label': 'To Do', 'icon': 'fa-circle-o', 'color': '#17a2b8', 'is_completed': False, 'is_active': False, 'next_statuses': ['IN_PROGRESS']},
    'IN_PROGRESS': {'label': 'In Progress', 'icon': 'fa-play', 'color': '#ffc107', 'is_completed': False, 'is_active': True, 'next_statuses': ['IN_REVIEW', 'BLOCKED']},
    'IN_REVIEW': {'label': 'In Review', 'icon': 'fa-eye', 'color': '#fd7e14', 'is_completed': False, 'is_active': True, 'next_statuses': ['TESTING', 'IN_PROGRESS']},
    'TESTING': {'label': 'Testing', 'icon': 'fa-flask', 'color': '#e83e8c', 'is_completed': False, 'is_active': True, 'next_statuses': ['DONE', 'IN_PROGRESS']},
    'DONE': {'label': 'Done', 'icon': 'fa-check', 'color': '#28a745', 'is_completed': True, 'is_active': False, 'next_statuses': ['DEPLOYED']},
    'DEPLOYED': {'label': 'Deployed', 'icon': 'fa-rocket', 'color': '#20c997', 'is_completed': True, 'is_active': False, 'next_statuses': []},
    'BLOCKED': {'label': 'Blocked', 'icon': 'fa-ban', 'color': '#dc3545', 'is_completed': False, 'is_active': False, 'next_statuses': ['IN_PROGRESS']},
    'CANCELLED': {'label': 'Cancelled', 'icon': 'fa-times', 'color': '#6c757d', 'is_completed': True, 'is_active': False, 'next_statuses': []}
}

USER_ROLE_CONFIG = {
    'ADMIN': {'label': 'Administrator', 'icon': 'fa-crown', 'color': '#dc3545', 'hierarchy_level': 10, 'permissions': ['all']},
    'PROJECT_MANAGER': {'label': 'Project Manager', 'icon': 'fa-users', 'color': '#007bff', 'hierarchy_level': 9, 'permissions': ['project_management']},
    'TEAM_LEAD': {'label': 'Team Lead', 'icon': 'fa-user-tie', 'color': '#6f42c1', 'hierarchy_level': 8, 'permissions': ['team_management']},
    'SENIOR_DEVELOPER': {'label': 'Senior Developer', 'icon': 'fa-code', 'color': '#28a745', 'hierarchy_level': 7, 'permissions': ['development', 'review']},
    'DEVELOPER': {'label': 'Developer', 'icon': 'fa-laptop-code', 'color': '#17a2b8', 'hierarchy_level': 6, 'permissions': ['development']},
    'QA_ENGINEER': {'label': 'QA Engineer', 'icon': 'fa-check-double', 'color': '#fd7e14', 'hierarchy_level': 6, 'permissions': ['testing']},
    'DEVOPS_ENGINEER': {'label': 'DevOps Engineer', 'icon': 'fa-server', 'color': '#20c997', 'hierarchy_level': 7, 'permissions': ['deployment', 'infrastructure']},
    'UI_UX_DESIGNER': {'label': 'UI/UX Designer', 'icon': 'fa-paint-brush', 'color': '#e83e8c', 'hierarchy_level': 6, 'permissions': ['design']},
    'BUSINESS_ANALYST': {'label': 'Business Analyst', 'icon': 'fa-chart-line', 'color': '#ffc107', 'hierarchy_level': 7, 'permissions': ['analysis']},
    'PRODUCT_OWNER': {'label': 'Product Owner', 'icon': 'fa-bullseye', 'color': '#6f42c1', 'hierarchy_level': 8, 'permissions': ['product_management']},
    'SCRUM_MASTER': {'label': 'Scrum Master', 'icon': 'fa-clipboard-list', 'color': '#fd7e14', 'hierarchy_level': 7, 'permissions': ['scrum_management']}
}

PROJECT_STATUS_CONFIG = {
    'PLANNING': {'label': 'Planning', 'icon': 'fa-clipboard', 'color': '#ffc107', 'is_active': False, 'allows_new_tasks': True},
    'ACTIVE': {'label': 'Active', 'icon': 'fa-play', 'color': '#28a745', 'is_active': True, 'allows_new_tasks': True},
    'ON_HOLD': {'label': 'On Hold', 'icon': 'fa-pause', 'color': '#fd7e14', 'is_active': False, 'allows_new_tasks': False},
    'COMPLETED': {'label': 'Completed', 'icon': 'fa-check', 'color': '#20c997', 'is_active': False, 'allows_new_tasks': False},
    'CANCELLED': {'label': 'Cancelled', 'icon': 'fa-times', 'color': '#dc3545', 'is_active': False, 'allows_new_tasks': False}
}

SPRINT_STATUS_CONFIG = {
    'PLANNED': {'label': 'Planned', 'icon': 'fa-calendar', 'color': '#6c757d', 'is_active': False, 'allows_task_changes': True},
    'ACTIVE': {'label': 'Active', 'icon': 'fa-play', 'color': '#28a745', 'is_active': True, 'allows_task_changes': True},
    'COMPLETED': {'label': 'Completed', 'icon': 'fa-check', 'color': '#20c997', 'is_active': False, 'allows_task_changes': False},
    'CANCELLED': {'label': 'Cancelled', 'icon': 'fa-times', 'color': '#dc3545', 'is_active': False, 'allows_task_changes': False}
}

ESTIMATION_UNIT_CONFIG = {
    'STORY_POINTS': {'label': 'Story Points', 'icon': 'fa-star', 'color': '#007bff', 'conversion_factor': 1.0, 'default_value': 5},
    'HOURS': {'label': 'Hours', 'icon': 'fa-clock', 'color': '#28a745', 'conversion_factor': 8.0, 'default_value': 4},
    'DAYS': {'label': 'Days', 'icon': 'fa-calendar-day', 'color': '#ffc107', 'conversion_factor': 64.0, 'default_value': 1}
}

def transform_enum_to_rich_objects(enum_class, config_dict, default_config):
    """Transform enum to rich objects with metadata."""
    result = []
    for item in enum_class:
        config = config_dict.get(item.value, {
            'label': format_label(item.value),
            **default_config
        })
        
        enum_obj = {'value': item.value}
        enum_obj.update(config)
        result.append(enum_obj)
    
    return result

def get_all_enums():
    """Returns all enums with rich metadata for frontend."""
    return {
        'user_roles': transform_enum_to_rich_objects(
            UserRole, 
            USER_ROLE_CONFIG, 
            {'icon': 'fa-user', 'color': '#6c757d', 'hierarchy_level': 5, 'permissions': []}
        ),
        'task_statuses': transform_enum_to_rich_objects(
            TaskStatus, 
            TASK_STATUS_CONFIG, 
            {'icon': 'fa-circle', 'color': '#6c757d', 'is_completed': False, 'is_active': False, 'next_statuses': []}
        ),
        'task_priorities': transform_enum_to_rich_objects(
            TaskPriority, 
            TASK_PRIORITY_CONFIG, 
            {'icon': 'fa-minus', 'color': '#6c757d', 'severity_level': 2, 'escalation_hours': 72}
        ),
        'task_types': transform_enum_to_rich_objects(
            TaskType, 
            TASK_TYPE_CONFIG, 
            {'icon': 'fa-tasks', 'color': '#6c757d', 'default_estimation_unit': 'STORY_POINTS', 'requires_approval': False}
        ),
        'project_statuses': transform_enum_to_rich_objects(
            ProjectStatus, 
            PROJECT_STATUS_CONFIG, 
            {'icon': 'fa-circle', 'color': '#6c757d', 'is_active': False, 'allows_new_tasks': False}
        ),
        'sprint_statuses': transform_enum_to_rich_objects(
            SprintStatus, 
            SPRINT_STATUS_CONFIG, 
            {'icon': 'fa-circle', 'color': '#6c757d', 'is_active': False, 'allows_task_changes': False}
        ),
        'estimation_units': transform_enum_to_rich_objects(
            EstimationUnit, 
            ESTIMATION_UNIT_CONFIG, 
            {'icon': 'fa-ruler', 'color': '#6c757d', 'conversion_factor': 1.0, 'default_value': 1}
        )
    }
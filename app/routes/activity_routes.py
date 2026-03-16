# app/routes/activity_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.activity_service import ActivityService
from app.utils.response import (
    success_response, error_response, not_found_response,
    validation_error_response, server_error_response,
)
from app.utils.logger import get_logger

logger = get_logger('api.activity')

activity_bp = Blueprint('activity', __name__, url_prefix='/api/activity')


# ── Task activity timeline ────────────────────────────────────────────────────

@activity_bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def task_activity(task_id):
    """Get activity timeline for a specific task."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    result, status_code = ActivityService.get_task_activity(task_id, page, per_page)

    if status_code == 404:
        return not_found_response(result.get('error', 'Task not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error fetching activity'),
                              status_code=status_code)

    return success_response("Task activity retrieved successfully", result)


# ── Project activity feed ─────────────────────────────────────────────────────

@activity_bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def project_activity(project_id):
    """Get activity feed for a project."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    result, status_code = ActivityService.get_project_activity(
        project_id, page, per_page
    )

    if status_code == 404:
        return not_found_response(result.get('error', 'Project not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error fetching activity'),
                              status_code=status_code)

    return success_response("Project activity retrieved successfully", result)


# ── User action history ───────────────────────────────────────────────────────

@activity_bp.route('/users/<int:target_user_id>', methods=['GET'])
@jwt_required()
def user_activity(target_user_id):
    """Get action history for a specific user."""
    requesting_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    result, status_code = ActivityService.get_user_activity(
        target_user_id, page, per_page
    )

    if status_code != 200:
        return error_response(result.get('error', 'Error fetching activity'),
                              status_code=status_code)

    return success_response("User activity retrieved successfully", result)


# ── Recent activity (global) ──────────────────────────────────────────────────

@activity_bp.route('/recent', methods=['GET'])
@jwt_required()
def recent_activity():
    """Get the most recent activity across all entities."""
    limit = min(request.args.get('limit', 50, type=int), 200)
    entity_type = request.args.get('entity_type')

    result, status_code = ActivityService.get_recent_activity(
        limit=limit, entity_type=entity_type
    )

    if status_code != 200:
        return error_response(result.get('error', 'Error fetching activity'),
                              status_code=status_code)

    return success_response("Recent activity retrieved successfully", result)


# ── Manual activity log entry ─────────────────────────────────────────────────

@activity_bp.route('', methods=['POST'])
@jwt_required()
def log_activity():
    """Manually log an activity entry."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    required = ['entity_type', 'entity_id', 'action']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return validation_error_response(
            f'Missing required fields: {", ".join(missing)}'
        )

    result, status_code = ActivityService.log_activity(
        user_id=user_id,
        entity_type=data['entity_type'],
        entity_id=int(data['entity_id']),
        action=data['action'],
        description=data.get('description'),
        field_name=data.get('field_name'),
        old_value=data.get('old_value'),
        new_value=data.get('new_value'),
        ip_address=request.remote_addr,
    )

    if status_code != 201:
        return error_response(result.get('error', 'Error logging activity'),
                              status_code=status_code)

    return success_response("Activity logged successfully", result)

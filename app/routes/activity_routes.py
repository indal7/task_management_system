# app/routes/activity_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.activity_service import ActivityService
from app.utils.response import (
    success_response, error_response, server_error_response
)
from app.utils.logger import get_logger

activity_bp = Blueprint('activity', __name__, url_prefix='/api/activity')
logger = get_logger('api.activity')


@activity_bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task_activity(task_id):
    """Get activity log for a specific task."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        result, status_code = ActivityService.get_task_activity(task_id, page=page, per_page=per_page)
        if status_code != 200:
            return error_response(result.get('error', 'Error fetching activity'), status_code=status_code)
        return success_response('Task activity retrieved successfully', result)
    except Exception as e:
        logger.error(f'Get task activity error: {str(e)}')
        return server_error_response(f'Error fetching task activity: {str(e)}')


@activity_bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project_activity(project_id):
    """Get activity log for a specific project."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        result, status_code = ActivityService.get_project_activity(project_id, page=page, per_page=per_page)
        if status_code != 200:
            return error_response(result.get('error', 'Error fetching activity'), status_code=status_code)
        return success_response('Project activity retrieved successfully', result)
    except Exception as e:
        logger.error(f'Get project activity error: {str(e)}')
        return server_error_response(f'Error fetching project activity: {str(e)}')


@activity_bp.route('/users/<int:target_user_id>', methods=['GET'])
@jwt_required()
def get_user_activity(target_user_id):
    """Get all activity performed by a specific user."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        result, status_code = ActivityService.get_user_activity(target_user_id, page=page, per_page=per_page)
        if status_code != 200:
            return error_response(result.get('error', 'Error fetching activity'), status_code=status_code)
        return success_response('User activity retrieved successfully', result)
    except Exception as e:
        logger.error(f'Get user activity error: {str(e)}')
        return server_error_response(f'Error fetching user activity: {str(e)}')

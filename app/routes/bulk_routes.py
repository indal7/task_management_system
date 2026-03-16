# app/routes/bulk_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.bulk_service import BulkService
from app.utils.response import (
    success_response, error_response, validation_error_response, server_error_response
)
from app.utils.logger import get_logger

bulk_bp = Blueprint('bulk', __name__, url_prefix='/api/tasks/bulk')
logger = get_logger('api.bulk')


@bulk_bp.route('/update', methods=['POST'])
@jwt_required()
def bulk_update():
    """Bulk update multiple tasks."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return validation_error_response('No data provided')
    task_ids = data.get('task_ids', [])
    updates = data.get('updates', {})
    if not task_ids:
        return validation_error_response('task_ids is required')
    if not updates:
        return validation_error_response('updates is required')
    try:
        result, status_code = BulkService.bulk_update(task_ids, updates, user_id)
        if status_code != 200:
            return error_response(result.get('error', 'Error in bulk update'), status_code=status_code)
        return success_response('Tasks updated successfully', result)
    except Exception as e:
        logger.error(f'Bulk update error: {str(e)}')
        return server_error_response(f'Error in bulk update: {str(e)}')


@bulk_bp.route('/delete', methods=['POST'])
@jwt_required()
def bulk_delete():
    """Bulk delete multiple tasks."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return validation_error_response('No data provided')
    task_ids = data.get('task_ids', [])
    if not task_ids:
        return validation_error_response('task_ids is required')
    try:
        result, status_code = BulkService.bulk_delete(task_ids, user_id)
        if status_code != 200:
            return error_response(result.get('error', 'Error in bulk delete'), status_code=status_code)
        return success_response('Tasks deleted successfully', result)
    except Exception as e:
        logger.error(f'Bulk delete error: {str(e)}')
        return server_error_response(f'Error in bulk delete: {str(e)}')


@bulk_bp.route('/assign', methods=['POST'])
@jwt_required()
def bulk_assign():
    """Bulk assign multiple tasks to a user."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return validation_error_response('No data provided')
    task_ids = data.get('task_ids', [])
    assignee_id = data.get('assignee_id')
    if not task_ids:
        return validation_error_response('task_ids is required')
    if not assignee_id:
        return validation_error_response('assignee_id is required')
    try:
        result, status_code = BulkService.bulk_assign(task_ids, assignee_id, user_id)
        if status_code != 200:
            return error_response(result.get('error', 'Error in bulk assign'), status_code=status_code)
        return success_response('Tasks assigned successfully', result)
    except Exception as e:
        logger.error(f'Bulk assign error: {str(e)}')
        return server_error_response(f'Error in bulk assign: {str(e)}')


@bulk_bp.route('/status', methods=['POST'])
@jwt_required()
def bulk_change_status():
    """Bulk change status of multiple tasks."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return validation_error_response('No data provided')
    task_ids = data.get('task_ids', [])
    status = data.get('status')
    if not task_ids:
        return validation_error_response('task_ids is required')
    if not status:
        return validation_error_response('status is required')
    try:
        result, status_code = BulkService.bulk_change_status(task_ids, status, user_id)
        if status_code != 200:
            return error_response(result.get('error', 'Error changing status'), status_code=status_code)
        return success_response('Task statuses updated successfully', result)
    except Exception as e:
        logger.error(f'Bulk status change error: {str(e)}')
        return server_error_response(f'Error changing status: {str(e)}')


@bulk_bp.route('/priority', methods=['POST'])
@jwt_required()
def bulk_change_priority():
    """Bulk change priority of multiple tasks."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return validation_error_response('No data provided')
    task_ids = data.get('task_ids', [])
    priority = data.get('priority')
    if not task_ids:
        return validation_error_response('task_ids is required')
    if not priority:
        return validation_error_response('priority is required')
    try:
        result, status_code = BulkService.bulk_change_priority(task_ids, priority, user_id)
        if status_code != 200:
            return error_response(result.get('error', 'Error changing priority'), status_code=status_code)
        return success_response('Task priorities updated successfully', result)
    except Exception as e:
        logger.error(f'Bulk priority change error: {str(e)}')
        return server_error_response(f'Error changing priority: {str(e)}')

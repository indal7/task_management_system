# app/routes/bulk_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.services.bulk_service import BulkOperationService
from app.utils.response import (
    success_response, error_response, not_found_response,
    validation_error_response, server_error_response,
)
from app.utils.logger import get_logger

logger = get_logger('api.bulk')

bulk_bp = Blueprint('bulk', __name__, url_prefix='/api/tasks/bulk')


def _get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user_id, user.role if user else None


# ── Bulk update ───────────────────────────────────────────────────────────────

@bulk_bp.route('/update', methods=['PATCH'])
@jwt_required()
def bulk_update():
    """
    Bulk update multiple tasks.

    Body:
      task_ids: [int, ...]
      updates: {
        status: str,
        priority: str,
        assigned_to_id: int|null,
        sprint_id: int|null,
      }
    """
    user_id, role = _get_current_user()
    data = request.get_json() or {}

    task_ids = data.get('task_ids')
    updates = data.get('updates')

    if not task_ids or not isinstance(task_ids, list):
        return validation_error_response('task_ids must be a non-empty list')
    if not updates or not isinstance(updates, dict):
        return validation_error_response('updates must be a non-empty object')

    result, status_code = BulkOperationService.bulk_update_tasks(
        task_ids, updates, user_id, role
    )

    if status_code == 404:
        return not_found_response(result.get('error', 'Tasks not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Bulk update failed'),
                              status_code=status_code)

    return success_response("Bulk update successful", result)


# ── Bulk delete ───────────────────────────────────────────────────────────────

@bulk_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def bulk_delete():
    """
    Bulk delete tasks.

    Body:
      task_ids: [int, ...]
    """
    user_id, role = _get_current_user()
    data = request.get_json() or {}

    task_ids = data.get('task_ids')
    if not task_ids or not isinstance(task_ids, list):
        return validation_error_response('task_ids must be a non-empty list')

    result, status_code = BulkOperationService.bulk_delete_tasks(
        task_ids, user_id, role
    )

    if status_code == 404:
        return not_found_response(result.get('error', 'Tasks not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Bulk delete failed'),
                              status_code=status_code)

    return success_response("Bulk delete successful", result)


# ── Bulk assign ───────────────────────────────────────────────────────────────

@bulk_bp.route('/assign', methods=['POST'])
@jwt_required()
def bulk_assign():
    """
    Bulk assign tasks to a user.

    Body:
      task_ids: [int, ...]
      assignee_id: int
    """
    user_id, role = _get_current_user()
    data = request.get_json() or {}

    task_ids = data.get('task_ids')
    assignee_id = data.get('assignee_id')

    if not task_ids or not isinstance(task_ids, list):
        return validation_error_response('task_ids must be a non-empty list')
    if not assignee_id:
        return validation_error_response('assignee_id is required')

    result, status_code = BulkOperationService.bulk_assign_tasks(
        task_ids, int(assignee_id), user_id, role
    )

    if status_code == 404:
        return not_found_response(result.get('error', 'Not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Bulk assign failed'),
                              status_code=status_code)

    return success_response("Bulk assign successful", result)


# ── Bulk change sprint ────────────────────────────────────────────────────────

@bulk_bp.route('/sprint', methods=['POST'])
@jwt_required()
def bulk_change_sprint():
    """
    Move multiple tasks to a sprint (or remove from sprint).

    Body:
      task_ids: [int, ...]
      sprint_id: int|null   (null to remove from sprint)
    """
    user_id, role = _get_current_user()
    data = request.get_json() or {}

    task_ids = data.get('task_ids')
    sprint_id = data.get('sprint_id')   # can be null

    if not task_ids or not isinstance(task_ids, list):
        return validation_error_response('task_ids must be a non-empty list')

    result, status_code = BulkOperationService.bulk_change_sprint(
        task_ids,
        int(sprint_id) if sprint_id is not None else None,
        user_id, role,
    )

    if status_code == 404:
        return not_found_response(result.get('error', 'Not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Bulk sprint change failed'),
                              status_code=status_code)

    return success_response("Bulk sprint change successful", result)

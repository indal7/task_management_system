# app/routes/search_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.search_service import SearchService
from app.utils.response import (
    success_response, error_response, validation_error_response, server_error_response
)
from app.utils.logger import get_logger

search_bp = Blueprint('search', __name__, url_prefix='/api/search')
logger = get_logger('api.search')


@search_bp.route('/global', methods=['GET'])
@jwt_required()
def global_search():
    """Global search across tasks, projects and users."""
    user_id = get_jwt_identity()
    try:
        q = request.args.get('q', '').strip()
        if not q:
            return validation_error_response('Search query is required')
        limit = min(request.args.get('limit', 10, type=int), 50)
        result, status_code = SearchService.global_search(q, user_id, limit=limit)
        if status_code != 200:
            return error_response(result.get('error', 'Error performing search'), status_code=status_code)
        return success_response('Search results retrieved', result)
    except Exception as e:
        logger.error(f'Global search error: {str(e)}')
        return server_error_response(f'Error performing search: {str(e)}')


@search_bp.route('/tasks', methods=['GET'])
@jwt_required()
def advanced_task_search():
    """Advanced task search with multiple filters."""
    user_id = get_jwt_identity()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        filters = {}
        filter_keys = [
            'q', 'project_id', 'sprint_id', 'assigned_to_id', 'created_by_id',
            'status', 'priority', 'task_type', 'due_date_from', 'due_date_to', 'overdue'
        ]
        for key in filter_keys:
            val = request.args.get(key)
            if val is not None:
                filters[key] = val

        # project_id and similar numeric filters should be integers
        for int_key in ('project_id', 'sprint_id', 'assigned_to_id', 'created_by_id'):
            if filters.get(int_key):
                try:
                    filters[int_key] = int(filters[int_key])
                except ValueError:
                    return validation_error_response(f'Invalid value for {int_key}')

        result, status_code = SearchService.advanced_task_search(filters, page=page, per_page=per_page)
        if status_code != 200:
            return error_response(result.get('error', 'Error searching tasks'), status_code=status_code)
        return success_response('Tasks retrieved successfully', result)
    except Exception as e:
        logger.error(f'Advanced task search error: {str(e)}')
        return server_error_response(f'Error searching tasks: {str(e)}')

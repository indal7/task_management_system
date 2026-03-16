# app/routes/search_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.search_service import SearchService
from app.utils.response import (
    success_response, error_response, validation_error_response,
    server_error_response,
)
from app.utils.logger import get_logger

logger = get_logger('api.search')

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


# ── Global search ─────────────────────────────────────────────────────────────

@search_bp.route('/global', methods=['GET'])
@jwt_required()
def global_search():
    """
    Global search across tasks, projects, users, and sprints.

    Query params:
      q          - search query (required)
      types      - comma-separated entity types to search
                   (default: tasks,projects,users,sprints)
      limit      - max results per entity type (default 10)
    """
    user_id = get_jwt_identity()
    q = request.args.get('q', '').strip()
    if not q:
        return validation_error_response('Query parameter "q" is required')

    types_param = request.args.get('types', '')
    entity_types = [t.strip() for t in types_param.split(',') if t.strip()] \
        if types_param else None

    limit = request.args.get('limit', 10, type=int)

    try:
        result, status_code = SearchService.global_search(
            query_str=q,
            user_id=user_id,
            entity_types=entity_types,
            limit=limit,
        )

        if status_code != 200:
            return error_response(result.get('error', 'Search failed'),
                                  status_code=status_code)

        return success_response("Search results", result)

    except Exception as e:
        logger.error(f"Global search error: {e}")
        return server_error_response(f'Search error: {str(e)}')


# ── Advanced task search ──────────────────────────────────────────────────────

@search_bp.route('/tasks', methods=['GET'])
@jwt_required()
def advanced_task_search():
    """
    Advanced task search with complex filters.

    Query params:
      q            - keyword to search in title and description
      status       - task status (single or comma-separated)
      priority     - task priority (single or comma-separated)
      task_type    - task type (single or comma-separated)
      project_id   - filter by project
      sprint_id    - filter by sprint
      assigned_to_id
      created_by_id
      labels       - comma-separated labels to match
      due_before   - ISO datetime string
      due_after    - ISO datetime string
      overdue      - true/false
      page, per_page, sort_by, sort_order
    """
    user_id = get_jwt_identity()

    filters = {
        'q': request.args.get('q'),
        'status': request.args.get('status'),
        'priority': request.args.get('priority'),
        'task_type': request.args.get('task_type'),
        'project_id': request.args.get('project_id'),
        'sprint_id': request.args.get('sprint_id'),
        'assigned_to_id': request.args.get('assigned_to_id'),
        'created_by_id': request.args.get('created_by_id'),
        'labels': request.args.get('labels'),
        'due_before': request.args.get('due_before'),
        'due_after': request.args.get('due_after'),
        'overdue': request.args.get('overdue'),
    }
    # Remove None entries
    filters = {k: v for k, v in filters.items() if v is not None}

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')

    try:
        result, status_code = SearchService.advanced_task_search(
            user_id=user_id,
            filters=filters,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        if status_code != 200:
            return error_response(result.get('error', 'Search failed'),
                                  status_code=status_code)

        return success_response("Task search results", result)

    except Exception as e:
        logger.error(f"Advanced task search error: {e}")
        return server_error_response(f'Search error: {str(e)}')

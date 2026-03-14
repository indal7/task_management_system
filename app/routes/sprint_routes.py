# app/routes/sprint_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.sprint_service import SprintService
from app.utils.response import (
    success_response, error_response, created_response, 
    not_found_response, validation_error_response, server_error_response
)
from app.utils.logger import get_logger, log_api_request, log_cache_operation
from app.utils.cache_utils import cache, cached_per_user, CacheKeys, invalidate_user_cache, invalidate_project_cache
import json

sprint_bp = Blueprint('sprint', __name__, url_prefix='/api/sprints')
logger = get_logger('api.sprints')


def cache_result(key, fetch_func, timeout=300):
    """Helper to fetch from cache or get fresh"""
    cached_data = cache.get(key)
    log_cache_operation("GET", key, hit=bool(cached_data))
    if cached_data:
        logger.info(f"Cache hit for {key}")
        return json.loads(cached_data)
    data = fetch_func()
    cache.set(key, json.dumps(data), timeout=timeout)
    log_cache_operation("SET", key)
    logger.info(f"Cache set for {key}")
    return data


@sprint_bp.route('', methods=['POST'])
@jwt_required()
def create_sprint():
    user_id = get_jwt_identity()
    data = request.get_json()
    log_api_request('/api/sprints', 'POST', user_id, request.remote_addr)

    if not data:
        logger.warning(f"Sprint creation failed: no data provided | User: {user_id}")
        return validation_error_response('No data provided')

    required_fields = ['name', 'project_id', 'start_date', 'end_date']
    for field in required_fields:
        if not data.get(field):
            logger.warning(f"Sprint creation failed: missing field {field} | User: {user_id}")
            return validation_error_response(f'Missing required field: {field}')

    result, status_code = SprintService.create_sprint(data, user_id)
    if status_code != 201:
        logger.warning(f"Sprint creation failed | User: {user_id}: {result.get('error')}")
        return error_response(result.get('error', 'Error creating sprint'), status_code=status_code)

    logger.info(f"Sprint created successfully | Sprint: {result.get('id')} | User: {user_id}")
    if data.get('project_id'):
        invalidate_project_cache(data['project_id'])

    return created_response("Sprint created successfully", result)


@sprint_bp.route('/<int:sprint_id>', methods=['GET'])
@jwt_required()
def get_sprint(sprint_id):
    user_id = get_jwt_identity()
    log_api_request(f'/api/sprints/{sprint_id}', 'GET', user_id, request.remote_addr)

    include_tasks = request.args.get('include_tasks', 'false').lower() == 'true'

    def fetch():
        result, status_code = SprintService.get_sprint_by_id(sprint_id, include_tasks)
        if status_code != 200:
            raise Exception(result.get('error', 'Error fetching sprint'))
        return result

    try:
        result = cache_result(f"sprint:{sprint_id}", fetch)
        logger.info(f"Sprint retrieved | Sprint: {sprint_id} | User: {user_id}")
        return success_response("Sprint retrieved successfully", result)
    except Exception as e:
        logger.error(f"Sprint fetch error | Sprint: {sprint_id} | User: {user_id} | {str(e)}")
        return server_error_response(f'Error fetching sprint: {str(e)}')


@sprint_bp.route('/<int:sprint_id>', methods=['PUT'])
@jwt_required()
def update_sprint(sprint_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    log_api_request(f'/api/sprints/{sprint_id}', 'PUT', user_id, request.remote_addr)

    if not data:
        logger.warning(f"Sprint update failed: no data provided | Sprint: {sprint_id} | User: {user_id}")
        return validation_error_response('No data provided')

    result, status_code = SprintService.update_sprint(sprint_id, data, user_id)
    if status_code != 200:
        logger.warning(f"Sprint update failed | Sprint: {sprint_id} | User: {user_id} | {result.get('error')}")
        return error_response(result.get('error', 'Error updating sprint'), status_code=status_code)

    logger.info(f"Sprint updated successfully | Sprint: {sprint_id} | User: {user_id}")
    if result.get('project_id'):
        invalidate_project_cache(result['project_id'])
    cache.delete(f"sprint:{sprint_id}")
    return success_response("Sprint updated successfully", result)


@sprint_bp.route('/<int:sprint_id>', methods=['DELETE'])
@jwt_required()
def delete_sprint(sprint_id):
    user_id = get_jwt_identity()
    log_api_request(f'/api/sprints/{sprint_id}', 'DELETE', user_id, request.remote_addr)

    result, status_code = SprintService.delete_sprint(sprint_id, user_id)
    if status_code != 200:
        logger.warning(f"Sprint deletion failed | Sprint: {sprint_id} | User: {user_id} | {result.get('error')}")
        return error_response(result.get('error', 'Error deleting sprint'), status_code=status_code)

    logger.info(f"Sprint deleted successfully | Sprint: {sprint_id} | User: {user_id}")
    if result.get('project_id'):
        invalidate_project_cache(result['project_id'])
    cache.delete(f"sprint:{sprint_id}")
    return success_response("Sprint deleted successfully", result)


@sprint_bp.route('/project/<int:project_id>', methods=['GET'])
@jwt_required()
@cached_per_user(timeout=300, key_prefix="project_sprints")
def get_project_sprints(project_id):
    user_id = get_jwt_identity()
    log_api_request(f'/api/sprints/project/{project_id}', 'GET', user_id, request.remote_addr)

    result, status_code = SprintService.get_project_sprints(project_id, user_id)
    if status_code != 200:
        logger.warning(f"Project sprints fetch failed | Project: {project_id} | User: {user_id} | {result.get('error')}")
        return error_response(result.get('error', 'Error fetching project sprints'), status_code=status_code)

    logger.info(f"Project sprints retrieved | Project: {project_id} | User: {user_id} | Count: {len(result)}")
    return success_response("Project sprints retrieved successfully", result)


@sprint_bp.route('/<int:sprint_id>/burndown', methods=['GET'])
@jwt_required()
@cached_per_user(timeout=600, key_prefix="sprint_burndown")
def get_sprint_burndown(sprint_id):
    user_id = get_jwt_identity()
    log_api_request(f'/api/sprints/{sprint_id}/burndown', 'GET', user_id, request.remote_addr)

    result, status_code = SprintService.get_sprint_burndown(sprint_id, user_id)
    if status_code != 200:
        logger.warning(f"Sprint burndown fetch failed | Sprint: {sprint_id} | User: {user_id} | {result.get('error')}")
        return error_response(result.get('error', 'Error fetching burndown data'), status_code=status_code)

    logger.info(f"Sprint burndown data retrieved | Sprint: {sprint_id} | User: {user_id}")
    return success_response("Sprint burndown data retrieved successfully", result)

# app/routes/project_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.project_service import ProjectService
from app.utils.response import (
    success_response, error_response, created_response, 
    not_found_response, validation_error_response, server_error_response
)
from app.utils.logger import get_logger, log_cache_operation
from app.utils.cache_utils import cache
import json

project_bp = Blueprint('project', __name__, url_prefix='/api/projects')
logger = get_logger('project')


def cache_result(key, fetch_func, timeout=300):
    """Helper to get data from cache or fetch fresh"""
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


@project_bp.route('', methods=['POST'])
@jwt_required()
def create():
    data = request.get_json()
    user_id = get_jwt_identity()

    if not data.get('name'):
        logger.warning(f"Project creation failed: Missing name | User: {user_id}")
        return validation_error_response('Project name is required')

    result = ProjectService.create_project(data, user_id)
    logger.info(f"Project created successfully | Project: {result.get('id')} | User: {user_id}")
    cache.clear()  # Clear cache after creating new project
    return created_response("Project created successfully", result)


@project_bp.route('', methods=['GET'])
@jwt_required()
def get_all():
    try:
        result = cache_result("projects:all", ProjectService.get_all_projects)
        logger.info("All projects retrieved successfully")
        return success_response("Projects retrieved successfully", result)
    except Exception as e:
        logger.error(f"Error fetching all projects: {e}", exc_info=True)
        return server_error_response(f"Error fetching projects: {str(e)}")


@project_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_one(project_id):
    try:
        key = f"projects:{project_id}"
        result = cache_result(key, lambda: ProjectService.get_project_by_id(project_id))
        logger.info(f"Project retrieved | Project: {project_id}")
        return success_response("Project retrieved successfully", result)
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}", exc_info=True)
        return server_error_response(f"Error fetching project: {str(e)}")


@project_bp.route('/<int:project_id>', methods=['PATCH'])
@jwt_required()
def update(project_id):
    data = request.get_json()
    try:
        result = ProjectService.update_project(project_id, data)
        logger.info(f"Project updated successfully | Project: {project_id}")
        cache.delete(f"projects:{project_id}")  # Invalidate cache
        cache.delete("projects:all")  # Invalidate list cache
        return success_response("Project updated successfully", result)
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}", exc_info=True)
        return server_error_response(f"Error updating project: {str(e)}")


@project_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete(project_id):
    try:
        result = ProjectService.delete_project(project_id)
        logger.info(f"Project deleted | Project: {project_id}")
        cache.delete(f"projects:{project_id}")  # Invalidate cache
        cache.delete("projects:all")
        return success_response("Project deleted successfully", result)
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}", exc_info=True)
        return server_error_response(f"Error deleting project: {str(e)}")


@project_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent():
    try:
        result = cache_result("projects:recent", ProjectService.get_recent_projects)
        logger.info("Recent projects retrieved successfully")
        return success_response("Recent projects retrieved successfully", result)
    except Exception as e:
        logger.error(f"Error fetching recent projects: {e}", exc_info=True)
        return server_error_response(f"Error fetching recent projects: {str(e)}")

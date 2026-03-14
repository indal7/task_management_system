# app/routes/enum_routes.py
from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.models.enums import get_all_enums
from app.utils.response import (
    success_response, server_error_response
)
from app.utils.logger import get_logger, log_cache_operation
from app.utils.cache_utils import cache

enum_bp = Blueprint('enums', __name__, url_prefix='/api/enums')
logger = get_logger('api')  # or use 'enum' if you prefer a separate logger


def cache_enum(key, fetch_func, timeout=300):
    """Helper to fetch enum from cache or load fresh"""
    cached_data = cache.get(key)
    log_cache_operation("GET", key, hit=bool(cached_data))
    if cached_data:
        logger.info(f"Cache hit for {key}")
        return cached_data
    data = fetch_func()
    cache.set(key, data, timeout=timeout)
    log_cache_operation("SET", key)
    logger.info(f"Cache set for {key}")
    return data


@enum_bp.route('', methods=['GET'])
@jwt_required()
def get_all_enums_endpoint():
    try:
        data = cache_enum("enums:all", get_all_enums)
        logger.info("All enums retrieved")
        return success_response("All enums retrieved successfully", data)
    except Exception as e:
        logger.error(f"Error fetching all enums: {e}", exc_info=True)
        return server_error_response(f'Error fetching enums: {str(e)}')


@enum_bp.route('/user-roles', methods=['GET'])
@jwt_required()
def get_user_roles():
    try:
        from app.models.enums import UserRole, enum_to_dict
        data = cache_enum("enums:user_roles", lambda: enum_to_dict(UserRole))
        logger.info("User roles retrieved")
        return success_response("User roles retrieved successfully", data)
    except Exception as e:
        logger.error(f"Error fetching user roles: {e}", exc_info=True)
        return server_error_response(f'Error fetching user roles: {str(e)}')


@enum_bp.route('/task-statuses', methods=['GET'])
@jwt_required()
def get_task_statuses():
    try:
        from app.models.enums import TaskStatus, enum_to_dict
        data = cache_enum("enums:task_statuses", lambda: enum_to_dict(TaskStatus))
        logger.info("Task statuses retrieved")
        return success_response("Task statuses retrieved successfully", data)
    except Exception as e:
        logger.error(f"Error fetching task statuses: {e}", exc_info=True)
        return server_error_response(f'Error fetching task statuses: {str(e)}')


@enum_bp.route('/task-priorities', methods=['GET'])
@jwt_required()
def get_task_priorities():
    try:
        from app.models.enums import TaskPriority, enum_to_dict
        data = cache_enum("enums:task_priorities", lambda: enum_to_dict(TaskPriority))
        logger.info("Task priorities retrieved")
        return success_response("Task priorities retrieved successfully", data)
    except Exception as e:
        logger.error(f"Error fetching task priorities: {e}", exc_info=True)
        return server_error_response(f'Error fetching task priorities: {str(e)}')


@enum_bp.route('/task-types', methods=['GET'])
@jwt_required()
def get_task_types():
    try:
        from app.models.enums import TaskType, enum_to_dict
        data = cache_enum("enums:task_types", lambda: enum_to_dict(TaskType))
        logger.info("Task types retrieved")
        return success_response("Task types retrieved successfully", data)
    except Exception as e:
        logger.error(f"Error fetching task types: {e}", exc_info=True)
        return server_error_response(f'Error fetching task types: {str(e)}')


@enum_bp.route('/project-statuses', methods=['GET'])
@jwt_required()
def get_project_statuses():
    try:
        from app.models.enums import ProjectStatus, enum_to_dict
        data = cache_enum("enums:project_statuses", lambda: enum_to_dict(ProjectStatus))
        logger.info("Project statuses retrieved")
        return success_response("Project statuses retrieved successfully", data)
    except Exception as e:
        logger.error(f"Error fetching project statuses: {e}", exc_info=True)
        return server_error_response(f'Error fetching project statuses: {str(e)}')


@enum_bp.route('/sprint-statuses', methods=['GET'])
@jwt_required()
def get_sprint_statuses():
    try:
        from app.models.enums import SprintStatus, enum_to_dict
        data = cache_enum("enums:sprint_statuses", lambda: enum_to_dict(SprintStatus))
        logger.info("Sprint statuses retrieved")
        return success_response("Sprint statuses retrieved successfully", data)
    except Exception as e:
        logger.error(f"Error fetching sprint statuses: {e}", exc_info=True)
        return server_error_response(f'Error fetching sprint statuses: {str(e)}')

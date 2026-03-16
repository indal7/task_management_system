# app/routes/analytics_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.analytics_service import AnalyticsService
from app.utils.response import (
    success_response, error_response, server_error_response
)
from app.utils.cache_utils import cache
from app.utils.logger import get_logger, log_cache_operation
from app.utils.decorators import log_request

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
logger = get_logger('analytics')


@analytics_bp.route('/task-completion', methods=['GET'])
@jwt_required()
@log_request
def task_completion():
    user_id = request.args.get('user_id', None)
    if not user_id:
        user_id = get_jwt_identity()

    period = request.args.get('period', 'month')
    cache_key = f"task_completion:{user_id}:{period}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))
    
    if cached_result:
        logger.info(f"Task completion fetched from cache | User: {user_id} | Period: {period}")
        return success_response("Task completion rate retrieved successfully (from cache)", cached_result)
    
    try:
        result = AnalyticsService.get_task_completion_rate(user_id, period)
        
        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                logger.warning(f"Task completion fetch failed | User: {user_id} | Status: {status_code}")
                return error_response(data.get('error', 'Error fetching task completion data'), status_code=status_code)
            result = data
        
        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info(f"Task completion fetched successfully | User: {user_id} | Period: {period}")
        return success_response("Task completion rate retrieved successfully", result)
        
    except Exception as e:
        logger.error(f"Error fetching task completion | User: {user_id} | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching task completion data: {str(e)}')


@analytics_bp.route('/user-productivity', methods=['GET'])
@jwt_required()
@log_request
def user_productivity():
    user_id = request.args.get('user_id', None)
    if not user_id:
        user_id = get_jwt_identity()
    
    cache_key = f"user_productivity:{user_id}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))
    
    if cached_result:
        logger.info(f"User productivity fetched from cache | User: {user_id}")
        return success_response("User productivity data retrieved successfully (from cache)", cached_result)
    
    try:
        result = AnalyticsService.get_user_performance(user_id)
        
        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                logger.warning(f"User productivity fetch failed | User: {user_id} | Status: {status_code}")
                return error_response(data.get('error', 'Error fetching user productivity data'), status_code=status_code)
            result = data
        
        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info(f"User productivity fetched successfully | User: {user_id}")
        return success_response("User productivity data retrieved successfully", result)
        
    except Exception as e:
        logger.error(f"Error fetching user productivity | User: {user_id} | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching user productivity data: {str(e)}')


@analytics_bp.route('/task-status-distribution', methods=['GET'])
@jwt_required()
@log_request
def task_status_distribution():
    cache_key = "task_status_distribution"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))
    
    if cached_result:
        logger.info("Task status distribution fetched from cache")
        return success_response("Task status distribution retrieved successfully (from cache)", cached_result)
    
    try:
        result = AnalyticsService.get_task_distribution_by_status()
        
        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                logger.warning(f"Task status distribution fetch failed | Status: {status_code}")
                return error_response(data.get('error', 'Error fetching task status distribution'), status_code=status_code)
            result = data
        
        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info("Task status distribution fetched successfully")
        return success_response("Task status distribution retrieved successfully", result)
        
    except Exception as e:
        logger.error(f"Error fetching task status distribution | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching task status distribution: {str(e)}')


@analytics_bp.route('/task-priority-distribution', methods=['GET'])
@jwt_required()
@log_request
def task_priority_distribution():
    cache_key = "task_priority_distribution"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))
    
    if cached_result:
        logger.info("Task priority distribution fetched from cache")
        return success_response("Task priority distribution retrieved successfully (from cache)", cached_result)
    
    try:
        result = AnalyticsService.get_task_distribution_by_priority()
        
        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                logger.warning(f"Task priority distribution fetch failed | Status: {status_code}")
                return error_response(data.get('error', 'Error fetching task priority distribution'), status_code=status_code)
            result = data
        
        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info("Task priority distribution fetched successfully")
        return success_response("Task priority distribution retrieved successfully", result)
        
    except Exception as e:
        logger.error(f"Error fetching task priority distribution | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching task priority distribution: {str(e)}')


@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@log_request
def dashboard_summary():
    """Return a consolidated dashboard metrics object for the current user."""
    user_id = get_jwt_identity()
    cache_key = f"dashboard_summary:{user_id}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))

    if cached_result:
        logger.info(f"Dashboard summary fetched from cache | User: {user_id}")
        return success_response("Dashboard summary retrieved successfully (from cache)", cached_result)

    try:
        result = AnalyticsService.get_dashboard_summary(user_id)

        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                return error_response(data.get('error', 'Error fetching dashboard'), status_code=status_code)
            result = data

        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info(f"Dashboard summary fetched | User: {user_id}")
        return success_response("Dashboard summary retrieved successfully", result)

    except Exception as e:
        logger.error(f"Dashboard summary error | User: {user_id} | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching dashboard summary: {str(e)}')


@analytics_bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
@log_request
def project_analytics(project_id):
    """Return analytics for a specific project."""
    cache_key = f"project_analytics:{project_id}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))

    if cached_result:
        logger.info(f"Project analytics fetched from cache | Project: {project_id}")
        return success_response("Project analytics retrieved successfully (from cache)", cached_result)

    try:
        result = AnalyticsService.get_project_analytics(project_id)

        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                return error_response(data.get('error', 'Error fetching project analytics'), status_code=status_code)
            result = data

        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info(f"Project analytics fetched | Project: {project_id}")
        return success_response("Project analytics retrieved successfully", result)

    except Exception as e:
        logger.error(f"Project analytics error | Project: {project_id} | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching project analytics: {str(e)}')


@analytics_bp.route('/sprints/<int:sprint_id>', methods=['GET'])
@jwt_required()
@log_request
def sprint_metrics(sprint_id):
    """Return performance metrics for a specific sprint."""
    cache_key = f"sprint_metrics:{sprint_id}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))

    if cached_result:
        logger.info(f"Sprint metrics fetched from cache | Sprint: {sprint_id}")
        return success_response("Sprint metrics retrieved successfully (from cache)", cached_result)

    try:
        result = AnalyticsService.get_sprint_metrics(sprint_id)

        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                return error_response(data.get('error', 'Error fetching sprint metrics'), status_code=status_code)
            result = data

        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info(f"Sprint metrics fetched | Sprint: {sprint_id}")
        return success_response("Sprint metrics retrieved successfully", result)

    except Exception as e:
        logger.error(f"Sprint metrics error | Sprint: {sprint_id} | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching sprint metrics: {str(e)}')


@analytics_bp.route('/velocity', methods=['GET'])
@jwt_required()
@log_request
def team_velocity():
    """Return team velocity over recent completed sprints."""
    project_id = request.args.get('project_id', type=int)
    num_sprints = request.args.get('num_sprints', 5, type=int)

    cache_key = f"team_velocity:{project_id}:{num_sprints}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))

    if cached_result:
        logger.info(f"Team velocity fetched from cache")
        return success_response("Team velocity retrieved successfully (from cache)", cached_result)

    try:
        result = AnalyticsService.get_team_velocity(project_id=project_id, num_sprints=num_sprints)

        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                return error_response(data.get('error', 'Error fetching velocity'), status_code=status_code)
            result = data

        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info(f"Team velocity fetched")
        return success_response("Team velocity retrieved successfully", result)

    except Exception as e:
        logger.error(f"Team velocity error | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching team velocity: {str(e)}')

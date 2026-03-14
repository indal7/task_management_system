# app/routes/analytics_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.analytics_service import AnalyticsService
from app.utils.response import (
    success_response, error_response, server_error_response
)
from app.utils.cache_utils import cache
from app.utils.logger import get_logger, log_request, log_cache_operation

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

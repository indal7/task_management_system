# app/routes/analytics_routes.py
from flask import Blueprint, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.analytics_service import AnalyticsService
from app.utils.response import (
    success_response, error_response, server_error_response
)
from app.utils.cache_utils import cache
from app.utils.logger import get_logger, log_cache_operation
from app.utils.decorators import log_request
import csv
import io

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
logger = get_logger('analytics')


@analytics_bp.route('/task-completion', methods=['GET'])
@jwt_required()
@log_request
def task_completion():
    user_id = request.args.get('user_id', None)
    if not user_id:
        user_id = get_jwt_identity()

    period = request.args.get('period') or request.args.get('time_period') or 'month'
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


@analytics_bp.route('/team-performance', methods=['GET'])
@jwt_required()
@log_request
def team_performance():
    """Get team-wide performance metrics (TeamPerformanceMetrics)."""
    cache_key = "team_performance"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))

    if cached_result:
        logger.info("Team performance fetched from cache")
        return success_response("Team performance retrieved successfully (from cache)", cached_result)

    try:
        result = AnalyticsService.get_team_productivity()

        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                return error_response(data.get('error', 'Error fetching team performance'), status_code=status_code)
            result = data

        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info("Team performance fetched successfully")
        return success_response("Team performance retrieved successfully", result)

    except Exception as e:
        logger.error(f"Error fetching team performance | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching team performance: {str(e)}')


@analytics_bp.route('/project-analytics', methods=['GET'])
@jwt_required()
@log_request
def project_analytics():
    """Get analytics for projects (ProjectAnalytics[])."""
    project_id = request.args.get('project_id', type=int)
    cache_key = f"project_analytics:{project_id or 'all'}"
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
        logger.info("Project analytics fetched successfully")
        return success_response("Project analytics retrieved successfully", result)

    except Exception as e:
        logger.error(f"Error fetching project analytics | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching project analytics: {str(e)}')


@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@log_request
def dashboard():
    """Get combined dashboard analytics for the current user."""
    user_id = request.args.get('user_id', None)
    if not user_id:
        user_id = get_jwt_identity()

    cache_key = f"dashboard_analytics:{user_id}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))

    if cached_result:
        logger.info(f"Dashboard analytics fetched from cache | User: {user_id}")
        return success_response("Dashboard analytics retrieved successfully (from cache)", cached_result)

    try:
        result = AnalyticsService.get_dashboard_analytics(user_id)

        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                return error_response(data.get('error', 'Error fetching dashboard analytics'), status_code=status_code)
            result = data

        cache.set(cache_key, result, timeout=180)
        log_cache_operation("SET", cache_key)
        logger.info(f"Dashboard analytics fetched successfully | User: {user_id}")
        return success_response("Dashboard analytics retrieved successfully", result)

    except Exception as e:
        logger.error(f"Error fetching dashboard analytics | User: {user_id} | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching dashboard analytics: {str(e)}')


@analytics_bp.route('/sprint-analytics', methods=['GET'])
@jwt_required()
@log_request
def sprint_analytics():
    """Get analytics for a specific sprint."""
    sprint_id = request.args.get('sprint_id', type=int)
    if not sprint_id:
        return error_response('sprint_id is required', status_code=400)

    cache_key = f"sprint_analytics:{sprint_id}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))

    if cached_result:
        logger.info(f"Sprint analytics fetched from cache | Sprint: {sprint_id}")
        return success_response("Sprint analytics retrieved successfully (from cache)", cached_result)

    try:
        result = AnalyticsService.get_sprint_analytics(sprint_id)

        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                return error_response(data.get('error', 'Error fetching sprint analytics'), status_code=status_code)
            result = data

        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info(f"Sprint analytics fetched successfully | Sprint: {sprint_id}")
        return success_response("Sprint analytics retrieved successfully", result)

    except Exception as e:
        logger.error(f"Error fetching sprint analytics | Sprint: {sprint_id} | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching sprint analytics: {str(e)}')


@analytics_bp.route('/comparison', methods=['GET'])
@jwt_required()
@log_request
def comparison():
    """Get comparison analytics (current vs previous period)."""
    user_id = request.args.get('user_id', None)
    if not user_id:
        user_id = get_jwt_identity()

    cache_key = f"comparison_analytics:{user_id}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))

    if cached_result:
        logger.info(f"Comparison analytics fetched from cache | User: {user_id}")
        return success_response("Comparison analytics retrieved successfully (from cache)", cached_result)

    try:
        result = AnalyticsService.get_comparison_analytics(user_id)

        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            if status_code != 200:
                return error_response(data.get('error', 'Error fetching comparison analytics'), status_code=status_code)
            result = data

        cache.set(cache_key, result, timeout=300)
        log_cache_operation("SET", cache_key)
        logger.info(f"Comparison analytics fetched successfully | User: {user_id}")
        return success_response("Comparison analytics retrieved successfully", result)

    except Exception as e:
        logger.error(f"Error fetching comparison analytics | User: {user_id} | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error fetching comparison analytics: {str(e)}')


@analytics_bp.route('/export', methods=['GET'])
@jwt_required()
def export_analytics():
    """Export analytics data as CSV."""
    user_id = get_jwt_identity()
    export_type = request.args.get('type', 'tasks')

    try:
        output = io.StringIO()
        writer = csv.writer(output)

        if export_type == 'tasks':
            from app.models.task import Task
            from app.models.enums import TaskStatus
            tasks = Task.query.filter_by(assigned_to_id=user_id).all()
            writer.writerow(['ID', 'Title', 'Status', 'Priority', 'Due Date', 'Created At'])
            for task in tasks:
                writer.writerow([
                    task.id,
                    task.title,
                    task.status.value if hasattr(task.status, 'value') else task.status,
                    task.priority.value if hasattr(task.priority, 'value') else task.priority,
                    task.due_date.isoformat() if task.due_date else '',
                    task.created_at.isoformat() if task.created_at else ''
                ])
        elif export_type == 'productivity':
            result = AnalyticsService.get_user_performance(user_id)
            if isinstance(result, list) and result:
                data = result[0]
                writer.writerow(['Metric', 'Value'])
                for key, value in data.items():
                    if not isinstance(value, (list, dict)):
                        writer.writerow([key, value])
        else:
            writer.writerow(['No data available for the requested export type'])

        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=analytics_{export_type}.csv'
        logger.info(f"Analytics exported | User: {user_id} | Type: {export_type}")
        return response

    except Exception as e:
        logger.error(f"Error exporting analytics | User: {user_id} | Error: {str(e)}", exc_info=True)
        return server_error_response(f'Error exporting analytics: {str(e)}')


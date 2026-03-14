# app/routes/task_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.models.task_comment import TaskComment
from app.models.user import User
from app.models.time_log import TimeLog
from app.services.task_service import TaskService
from app.utils.response import (
    success_response, error_response, created_response, 
    not_found_response, validation_error_response, server_error_response
)

# Import logging and caching utilities
from app.utils.logger import get_logger, log_api_request
from app.utils.cache_utils import cache, cached_per_user, CacheKeys, invalidate_user_cache

# Initialize logger for this module
logger = get_logger('api.tasks')

task_bp = Blueprint('task', __name__, url_prefix='/api/tasks')


@task_bp.route('', methods=['POST'])
@jwt_required()
def create():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Log API request
    log_api_request('/api/tasks', 'POST', user_id, request.remote_addr)
    logger.info(f"Creating task for user {user_id}")
    
    try:
        # Override user_id from JWT token for security
        data['user_id'] = user_id
        result = TaskService.create_task(data, user_id)

        if isinstance(result, tuple) and len(result) == 2 and 'error' in result[0]:
            logger.warning(f"Task creation failed for user {user_id}: {result[0]['error']}")
            return error_response(result[0]['error'], status_code=result[1])

        logger.info(f"Task created successfully by user {user_id}")
        return created_response("Task created successfully", result)

    except Exception as e:
        logger.error(f"Task creation error for user {user_id}: {str(e)}")
        return server_error_response(f'Error creating task: {str(e)}')


@task_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get tasks with advanced filtering and pagination."""
    user_id = get_jwt_identity()
    
    # Log API request
    log_api_request('/api/tasks', 'GET', user_id, request.remote_addr)
    logger.debug(f"Fetching tasks for user {user_id}")
    
    try:
        # Extract pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build filters from query parameters
        filters = {}
        
        # Project and sprint filters
        if request.args.get('project_id'):
            filters['project_id'] = int(request.args.get('project_id'))
            logger.debug(f"Filtering by project_id: {filters['project_id']}")
        if request.args.get('sprint_id'):
            filters['sprint_id'] = int(request.args.get('sprint_id'))
            
        # User filters
        if request.args.get('assigned_to_id'):
            filters['assigned_to_id'] = int(request.args.get('assigned_to_id'))
        if request.args.get('created_by_id'):
            filters['created_by_id'] = int(request.args.get('created_by_id'))
            
        # Status and priority filters
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('priority'):
            filters['priority'] = request.args.get('priority')
        if request.args.get('task_type'):
            filters['task_type'] = request.args.get('task_type')
            
        # Special filters
        if request.args.get('overdue') == 'true':
            filters['overdue'] = True
        if request.args.get('parent_task_id'):
            filters['parent_task_id'] = int(request.args.get('parent_task_id'))
        
        # Call service method
        result, status_code = TaskService.get_tasks_by_filters(user_id, filters)
        
        if status_code != 200:
            logger.warning(f"Task fetching failed for user {user_id}: {result.get('error', 'Unknown error')}")
            return error_response(result.get('error', 'Error fetching tasks'), status_code=status_code)
        
        # Apply pagination
        tasks = result
        total = len(tasks)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_tasks = tasks[start_index:end_index]
        
        response_data = {
            'data': paginated_tasks,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'has_next': end_index < total,
            'has_prev': page > 1
        }
        
        logger.debug(f"Retrieved {len(paginated_tasks)} tasks (page {page}) for user {user_id}")
        return success_response("Tasks retrieved successfully", response_data)
        
    except Exception as e:
        logger.error(f"Task fetching error for user {user_id}: {str(e)}")
        return server_error_response(f'Error fetching tasks: {str(e)}')


@task_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_one(task_id):
    user_id = get_jwt_identity()
    
    # Log API request
    log_api_request(f'/api/tasks/{task_id}', 'GET', user_id, request.remote_addr)
    logger.debug(f"Fetching task {task_id} for user {user_id}")
    
    try:
        result, status_code = TaskService.get_task_by_id(task_id, user_id)

        if status_code != 200 or 'error' in result:
            logger.warning(f"Task {task_id} fetch failed for user {user_id}: {result.get('error', 'Not found')}")
            return not_found_response(result.get('error', 'Task not found'))

        # Fetch all comments for the given task
        comments = TaskComment.query.filter_by(task_id=task_id).all()

        # Get unique user IDs from the comments
        user_ids = {comment.user_id for comment in comments}

        # Fetch user details in a single query
        users = User.query.filter(User.id.in_(user_ids)).all()
        user_map = {user.id: {"id": user.id, "name": user.name, "email": user.email} for user in users}

        # Attach user details to comments
        result['comments'] = [
            {
                **comment.to_dict(),
                "author": user_map.get(comment.user_id, {})
            } for comment in comments
        ]

        logger.debug(f"Task {task_id} retrieved successfully with {len(comments)} comments")
        return success_response("Task retrieved successfully", result)

    except Exception as e:
        logger.error(f"Task {task_id} fetch error for user {user_id}: {str(e)}")
        return server_error_response(f'Error fetching task: {str(e)}')


@task_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update(task_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Log API request
    log_api_request(f'/api/tasks/{task_id}', 'PUT', user_id, request.remote_addr)
    logger.info(f"Updating task {task_id} by user {user_id}")
    
    try:
        result, status_code = TaskService.update_task(task_id, data, user_id)

        if status_code != 200 or 'error' in result:
            logger.warning(f"Task {task_id} update failed for user {user_id}: {result.get('error', 'Unknown error')}")
            return error_response(result.get('error', 'Error updating task'), status_code=status_code)

        logger.info(f"Task {task_id} updated successfully by user {user_id}")
        return success_response("Task updated successfully", result)

    except Exception as e:
        logger.error(f"Task {task_id} update error for user {user_id}: {str(e)}")
        return server_error_response(f'Error updating task: {str(e)}')


@task_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete(task_id):
    user_id = get_jwt_identity()
    
    # Log API request
    log_api_request(f'/api/tasks/{task_id}', 'DELETE', user_id, request.remote_addr)
    logger.info(f"Deleting task {task_id} by user {user_id}")
    
    try:
        result, status_code = TaskService.delete_task(task_id, user_id)
        
        if status_code != 200 or 'error' in result:
            logger.warning(f"Task {task_id} deletion failed for user {user_id}: {result.get('error', 'Unknown error')}")
            return error_response(result.get('error', 'Error deleting task'), status_code=status_code)

        logger.info(f"Task {task_id} deleted successfully by user {user_id}")
        return success_response("Task deleted successfully")

    except Exception as e:
        logger.error(f"Task {task_id} deletion error for user {user_id}: {str(e)}")
        return server_error_response(f'Error deleting task: {str(e)}')


@task_bp.route('/<int:task_id>/assign', methods=['POST'])
@jwt_required()
def assign(task_id):
    assigner_id = get_jwt_identity()
    data = request.get_json()
    
    # Log API request
    log_api_request(f'/api/tasks/{task_id}/assign', 'POST', assigner_id, request.remote_addr)
    logger.info(f"Assigning task {task_id} by user {assigner_id}")
    
    try:
        user_id = data.get('user_id')
        if not user_id:
            logger.warning(f"Task {task_id} assignment failed: missing user_id")
            return validation_error_response('Missing user_id')

        result, status_code = TaskService.assign_task(task_id, user_id, assigner_id)

        if status_code != 200 or 'error' in result:
            logger.warning(f"Task {task_id} assignment failed: {result.get('error', 'Unknown error')}")
            return error_response(result.get('error', 'Error assigning task'), status_code=status_code)

        # Fetch updated task details
        task_result, task_status = TaskService.get_task_by_id(task_id, assigner_id)
        if task_status == 200:
            comments = TaskComment.query.filter_by(task_id=task_id).all()
            task_result['comments'] = [comment.to_dict() for comment in comments]
            
            logger.info(f"Task {task_id} assigned successfully to user {user_id}")
            return success_response("Task assigned successfully", task_result)
        
        return success_response("Task assigned successfully", result)

    except Exception as e:
        logger.error(f"Task {task_id} assignment error: {str(e)}")
        return server_error_response(f'Error assigning task: {str(e)}')


@task_bp.route('/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(task_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    # Log API request
    log_api_request(f'/api/tasks/{task_id}/comments', 'POST', user_id, request.remote_addr)
    logger.info(f"Adding comment to task {task_id} by user {user_id}")

    try:
        if not data:
            logger.warning(f"Comment addition failed for task {task_id}: no JSON payload")
            return validation_error_response('No JSON payload received')

        comment_text = data.get("text", "").strip()

        if not comment_text:
            logger.warning(f"Comment addition failed for task {task_id}: empty comment text")
            return validation_error_response('Comment text is required')

        result, status_code = TaskService.add_comment(task_id, user_id, comment_text)

        if status_code != 201 or 'error' in result:
            logger.warning(f"Comment addition failed for task {task_id}: {result.get('error', 'Unknown error')}")
            return error_response(result.get('error', 'Error adding comment'), status_code=status_code)

        logger.info(f"Comment added successfully to task {task_id} by user {user_id}")
        return created_response("Comment added successfully", result)

    except Exception as e:
        logger.error(f"Comment addition error for task {task_id}: {str(e)}")
        return server_error_response(f'Error adding comment: {str(e)}')


@task_bp.route('/overdue', methods=['GET'])
@jwt_required()
@cached_per_user(timeout=300, key_prefix="overdue_tasks")
def get_overdue_tasks():
    """Get overdue tasks for the current user."""
    user_id = get_jwt_identity()
    
    # Log API request
    log_api_request('/api/tasks/overdue', 'GET', user_id, request.remote_addr)
    logger.debug(f"Fetching overdue tasks for user {user_id}")
    
    try:
        result, status_code = TaskService.get_overdue_tasks(user_id)
        
        if status_code != 200:
            logger.warning(f"Overdue tasks fetch failed for user {user_id}: {result.get('error', 'Unknown error')}")
            return error_response(result.get('error', 'Error fetching overdue tasks'), status_code=status_code)
        
        logger.debug(f"Retrieved {len(result)} overdue tasks for user {user_id}")
        return success_response("Overdue tasks retrieved successfully", result)
        
    except Exception as e:
        logger.error(f"Overdue tasks fetch error for user {user_id}: {str(e)}")
        return server_error_response(f'Error fetching overdue tasks: {str(e)}')
    

@task_bp.route('/time-logs', methods=['GET'])
@jwt_required()
@cached_per_user(timeout=180, key_prefix="user_time_logs")
def get_user_time_logs():
    """Get time logs for the current user."""
    user_id = get_jwt_identity()
    
    # Log API request
    log_api_request('/api/tasks/time-logs', 'GET', user_id, request.remote_addr)
    logger.debug(f"Fetching time logs for user {user_id}")
    
    try:
        # Get date range parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)
        
        result, status_code = TaskService.get_user_time_logs(user_id, start_date, end_date, limit)
        
        if status_code != 200:
            logger.warning(f"Time logs fetch failed for user {user_id}: {result.get('error', 'Unknown error')}")
            return error_response(result.get('error', 'Error fetching time logs'), status_code=status_code)
        
        logger.debug(f"Retrieved {result.get('total_entries', 0)} time log entries for user {user_id}")
        return success_response("Time logs retrieved successfully", result)
        
    except Exception as e:
        logger.error(f"Time logs fetch error for user {user_id}: {str(e)}")
        return server_error_response(f'Error fetching time logs: {str(e)}')
    

@task_bp.route('/<int:task_id>/time', methods=['POST'])
@jwt_required()
def log_time_for_task(task_id):
    """Log time spent on a specific task."""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Log API request
    log_api_request(f'/api/tasks/{task_id}/time', 'POST', user_id, request.remote_addr)
    logger.info(f"Logging time for task {task_id} by user {user_id}")
    
    try:
        if not data:
            logger.warning(f"Time logging failed for task {task_id}: no data provided")
            return validation_error_response('No data provided')
            
        hours = data.get('hours')
        description = data.get('description', '')
        work_date = data.get('work_date')
        
        if not hours or hours <= 0:
            logger.warning(f"Time logging failed for task {task_id}: invalid hours value")
            return validation_error_response('Valid hours (> 0) are required')
            
        result, status_code = TaskService.log_time(task_id, user_id, hours, description, work_date)
        
        if status_code != 201:
            logger.warning(f"Time logging failed for task {task_id}: {result.get('error', 'Unknown error')}")
            return error_response(result.get('error', 'Error logging time'), status_code=status_code)
        
        # Invalidate time logs cache for user
        invalidate_user_cache(user_id, "user_time_logs")
        
        logger.info(f"Time logged successfully for task {task_id}: {hours} hours by user {user_id}")
        return created_response("Time logged successfully", result)
        
    except Exception as e:
        logger.error(f"Time logging error for task {task_id}: {str(e)}")
        return server_error_response(f'Error logging time: {str(e)}')


@task_bp.route('/<int:task_id>/time', methods=['GET'])
@jwt_required()
def get_task_time_logs(task_id):
    """Get time logs for a specific task."""
    user_id = get_jwt_identity()
    
    # Log API request
    log_api_request(f'/api/tasks/{task_id}/time', 'GET', user_id, request.remote_addr)
    logger.debug(f"Fetching time logs for task {task_id} by user {user_id}")
    
    try:
        result, status_code = TaskService.get_task_time_logs(task_id, user_id)
        
        if status_code != 200:
            logger.warning(f"Task time logs fetch failed for task {task_id}: {result.get('error', 'Unknown error')}")
            return error_response(result.get('error', 'Error fetching time logs'), status_code=status_code)
        
        logger.debug(f"Retrieved {len(result)} time log entries for task {task_id}")
        return success_response("Task time logs retrieved successfully", result)
        
    except Exception as e:
        logger.error(f"Task time logs fetch error for task {task_id}: {str(e)}")
        return server_error_response(f'Error fetching time logs: {str(e)}')


@task_bp.route('/time/daily-summary', methods=['GET'])
@jwt_required()
@cached_per_user(timeout=600, key_prefix="daily_time_summary")
def get_daily_time_summary():
    """Get daily time summary for the current user."""
    user_id = get_jwt_identity()
    
    # Log API request
    log_api_request('/api/tasks/time/daily-summary', 'GET', user_id, request.remote_addr)
    logger.debug(f"Fetching daily time summary for user {user_id}")
    
    try:
        date = request.args.get('date')
        
        if not date:
            date = datetime.utcnow().date().isoformat()
            
        daily_hours = TimeLog.get_user_daily_hours(user_id, date)
        
        response_data = {
            'date': date,
            'total_hours': daily_hours,
            'user_id': user_id
        }
        
        logger.debug(f"Daily summary for user {user_id} on {date}: {daily_hours} hours")
        return success_response("Daily summary retrieved successfully", response_data)
        
    except Exception as e:
        logger.error(f"Daily summary error for user {user_id}: {str(e)}")
        return server_error_response(f'Error fetching daily summary: {str(e)}')
    

@task_bp.route('/test-response', methods=['GET'])
def test_response():
    logger.debug("Testing response utilities")
    try:
        from app.utils.response import success_response
        return success_response("Test successful", {"test": "data"})
    except Exception as e:
        logger.error(f"Response utility test failed: {str(e)}")
        return jsonify({"error": f"Response utility error: {str(e)}"}), 500


# Import validation at module load
try:
    from app.utils.response import (
        success_response, error_response, created_response, 
        not_found_response, validation_error_response, server_error_response
    )
    logger.info("Response utilities imported successfully")
except ImportError as e:
    logger.error(f"Response utility import error: {e}")
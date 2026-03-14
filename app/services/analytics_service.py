# app/services/analytics_service.py
from app.models.task import Task
from app.models.user import User
from app.models.enums import TaskStatus
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
from app.utils.cache_utils import cache, cached_per_user, CacheKeys, invalidate_user_cache, invalidate_project_cache
from app.utils.logger import get_logger, log_db_query

logger = get_logger('analytics')


class AnalyticsService:

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.USER_ANALYTICS)
    def get_user_performance(user_id):
        """Returns task completion statistics for a specific user."""
        try:
            user = User.query.get_or_404(user_id)
            total_tasks = Task.query.filter_by(assigned_to_id=user.id).count()
            completed_tasks = Task.query.filter_by(
                assigned_to_id=user.id,
                status=TaskStatus.DONE.value
            ).count()
            completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0

            logger.info(f"User performance fetched for user {user.id}")
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': completion_rate
            }
        except Exception as e:
            logger.error(f"Error fetching user performance for user {user_id}: {str(e)}")
            return {'error': f'Error fetching user performance: {str(e)}'}, 500

    @staticmethod
    def get_team_productivity():
        """Returns productivity stats for all users."""
        try:
            users = User.query.all()
            team_stats = [
                {
                    'user': user.to_dict(),
                    'performance': AnalyticsService.get_user_performance(user.id)
                }
                for user in users
            ]
            logger.info(f"Team productivity stats fetched for {len(users)} users")
            return team_stats
        except Exception as e:
            logger.error(f"Error fetching team productivity: {str(e)}")
            return {'error': f'Error fetching team productivity: {str(e)}'}, 500

    @staticmethod
    def get_overdue_tasks():
        """Retrieves all tasks that are overdue but not yet completed."""
        try:
            tasks = Task.query.filter(
                Task.due_date.isnot(None),
                Task.due_date < datetime.utcnow(),
                Task.status != TaskStatus.DONE.value
            ).all()
            logger.info(f"Fetched {len(tasks)} overdue tasks")
            return [task.to_dict() for task in tasks]
        except Exception as e:
            logger.error(f"Error fetching overdue tasks: {str(e)}")
            return {'error': f'Error fetching overdue tasks: {str(e)}'}, 500

    @staticmethod
    def get_task_completion_rate(user_id, time_period='month'):
        """Returns task completion rate for a specific time period."""
        try:
            now = datetime.utcnow()
            if time_period == 'week':
                start_date = now - timedelta(days=7)
            elif time_period == 'month':
                start_date = now - timedelta(days=30)
            elif time_period == 'year':
                start_date = now - timedelta(days=365)
            else:
                return {'error': 'Invalid time period. Choose week, month, or year'}, 400

            total_tasks = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.created_at >= start_date
            ).count()

            completed_tasks = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.status == TaskStatus.DONE.value,
                Task.created_at >= start_date
            ).count()

            completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0

            logger.info(f"Task completion rate fetched for user {user_id} for {time_period}")
            return {
                'time_period': time_period,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': completion_rate,
                'start_date': start_date.isoformat(),
                'end_date': now.isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching task completion rate for user {user_id}: {str(e)}")
            return {'error': f'Error fetching task completion rate: {str(e)}'}, 500

    @staticmethod
    def get_task_distribution_by_status():
        """Returns distribution of tasks by their status."""
        try:
            distribution = Task.query.with_entities(Task.status, func.count(Task.id))\
                .group_by(Task.status).all()
            logger.info(f"Task distribution by status fetched")
            return {status.value if hasattr(status, 'value') else status: count for status, count in distribution}
        except Exception as e:
            logger.error(f"Error fetching task distribution by status: {str(e)}")
            return {'error': f'Error fetching task distribution by status: {str(e)}'}, 500

    @staticmethod
    def get_task_distribution_by_priority():
        """Returns distribution of tasks by their priority."""
        try:
            distribution = Task.query.with_entities(Task.priority, func.count(Task.id))\
                .group_by(Task.priority).all()
            logger.info(f"Task distribution by priority fetched")
            return {priority.value if hasattr(priority, 'value') else priority: count for priority, count in distribution}
        except Exception as e:
            logger.error(f"Error fetching task distribution by priority: {str(e)}")
            return {'error': f'Error fetching task distribution by priority: {str(e)}'}, 500

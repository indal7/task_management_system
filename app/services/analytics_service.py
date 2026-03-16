# app/services/analytics_service.py
from app.models.task import Task
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.time_log import TimeLog
from app.models.enums import TaskStatus, TaskPriority
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
        """Returns task completion statistics for a specific user (array format for frontend)."""
        try:
            user = User.query.get_or_404(user_id)
            total_tasks = Task.query.filter_by(assigned_to_id=user.id).count()
            completed_tasks = Task.query.filter_by(
                assigned_to_id=user.id,
                status=TaskStatus.DONE.value
            ).count()
            in_progress_tasks = Task.query.filter_by(
                assigned_to_id=user.id,
                status=TaskStatus.IN_PROGRESS.value
            ).count()
            overdue_tasks = Task.query.filter(
                Task.assigned_to_id == user.id,
                Task.due_date.isnot(None),
                Task.due_date < datetime.utcnow(),
                Task.status != TaskStatus.DONE.value
            ).count()
            completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

            # Calculate total hours logged
            total_hours = db.session.query(func.sum(TimeLog.hours)).filter(
                TimeLog.user_id == user.id
            ).scalar() or 0

            # Calculate average completion time from actual task data
            avg_completion_hours = 24.0
            if completed_tasks > 0 and total_hours > 0:
                avg_completion_hours = round(float(total_hours) / completed_tasks, 2)

            now = datetime.utcnow()
            start_date = now - timedelta(days=30)

            logger.info(f"User performance fetched for user {user.id}")
            # Return as array to match frontend UserProductivityAnalytics[] expectation
            return [{
                'user_id': user.id,
                'user_name': user.name,
                'user_email': user.email,
                'period': 'month',
                'start_date': start_date.isoformat(),
                'end_date': now.isoformat(),
                'total_tasks_assigned': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'overdue_tasks': overdue_tasks,
                'completion_rate': completion_rate,
                'average_completion_time_hours': avg_completion_hours,
                'total_hours_logged': float(total_hours),
                'daily_productivity': []
            }]
        except Exception as e:
            logger.error(f"Error fetching user performance for user {user_id}: {str(e)}")
            return {'error': f'Error fetching user performance: {str(e)}'}, 500

    @staticmethod
    def get_team_productivity():
        """Returns productivity stats for all users (TeamPerformanceMetrics format)."""
        try:
            users = User.query.all()
            if not users:
                return {
                    'team_size': 0,
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'average_completion_rate': 0,
                    'total_hours_logged': 0,
                    'average_hours_per_task': 0,
                    'most_productive_member': None,
                    'least_productive_member': None
                }

            total_tasks = Task.query.count()
            completed_tasks = Task.query.filter_by(status=TaskStatus.DONE.value).count()
            average_completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

            total_hours = db.session.query(func.sum(TimeLog.hours)).scalar() or 0
            average_hours_per_task = round(float(total_hours) / total_tasks, 2) if total_tasks > 0 else 0

            # Find most and least productive members
            user_rates = []
            for user in users:
                u_total = Task.query.filter_by(assigned_to_id=user.id).count()
                u_done = Task.query.filter_by(assigned_to_id=user.id, status=TaskStatus.DONE.value).count()
                rate = round((u_done / u_total * 100), 2) if u_total > 0 else 0
                user_rates.append({'user_id': user.id, 'user_name': user.name, 'completion_rate': rate})

            user_rates_sorted = sorted(user_rates, key=lambda x: x['completion_rate'], reverse=True)
            most_productive = user_rates_sorted[0] if user_rates_sorted else None
            least_productive = user_rates_sorted[-1] if len(user_rates_sorted) > 1 else user_rates_sorted[0] if user_rates_sorted else None

            logger.info(f"Team productivity stats fetched for {len(users)} users")
            return {
                'team_size': len(users),
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'average_completion_rate': average_completion_rate,
                'total_hours_logged': float(total_hours),
                'average_hours_per_task': average_hours_per_task,
                'most_productive_member': most_productive,
                'least_productive_member': least_productive
            }
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
        """Returns task completion rate for a specific time period (matches frontend TaskCompletionAnalytics)."""
        try:
            now = datetime.utcnow()
            if time_period == 'week' or time_period == 'weekly':
                start_date = now - timedelta(days=7)
                period_label = 'week'
            elif time_period == 'month' or time_period == 'monthly':
                start_date = now - timedelta(days=30)
                period_label = 'month'
            elif time_period == 'year' or time_period == 'yearly':
                start_date = now - timedelta(days=365)
                period_label = 'year'
            elif time_period == 'daily':
                start_date = now - timedelta(days=1)
                period_label = 'daily'
            else:
                start_date = now - timedelta(days=30)
                period_label = 'month'

            base_query = Task.query.filter(Task.assigned_to_id == user_id)

            total_tasks = base_query.filter(Task.created_at >= start_date).count()
            completed_tasks = base_query.filter(
                Task.status == TaskStatus.DONE.value,
                Task.created_at >= start_date
            ).count()

            completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

            # Build daily completion data for the period
            daily_completion = []
            days = (now - start_date).days + 1
            for i in range(min(days, 30)):
                day = start_date + timedelta(days=i)
                day_end = day + timedelta(days=1)
                day_completed = base_query.filter(
                    Task.status == TaskStatus.DONE.value,
                    Task.updated_at >= day,
                    Task.updated_at < day_end
                ).count()
                day_created = base_query.filter(
                    Task.created_at >= day,
                    Task.created_at < day_end
                ).count()
                daily_completion.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'completed': day_completed,
                    'created': day_created
                })

            logger.info(f"Task completion rate fetched for user {user_id} for {time_period}")
            return {
                'period': period_label,
                'time_period': period_label,
                'start_date': start_date.isoformat(),
                'end_date': now.isoformat(),
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': completion_rate,
                'daily_completion': daily_completion,
                'weekly_completion': [],
                'monthly_completion': []
            }
        except Exception as e:
            logger.error(f"Error fetching task completion rate for user {user_id}: {str(e)}")
            return {'error': f'Error fetching task completion rate: {str(e)}'}, 500

    @staticmethod
    def get_task_distribution_by_status():
        """Returns distribution of tasks by their status (TaskStatusDistribution[] format)."""
        try:
            distribution = Task.query.with_entities(Task.status, func.count(Task.id))\
                .group_by(Task.status).all()
            total = sum(count for _, count in distribution)
            result = []
            for status, count in distribution:
                status_val = status.value if hasattr(status, 'value') else str(status)
                result.append({
                    'status': status_val,
                    'count': count,
                    'percentage': round((count / total * 100), 2) if total > 0 else 0
                })
            logger.info("Task distribution by status fetched")
            return result
        except Exception as e:
            logger.error(f"Error fetching task distribution by status: {str(e)}")
            return {'error': f'Error fetching task distribution by status: {str(e)}'}, 500

    @staticmethod
    def get_task_distribution_by_priority():
        """Returns distribution of tasks by their priority (TaskPriorityDistribution[] format)."""
        try:
            distribution = Task.query.with_entities(Task.priority, func.count(Task.id))\
                .group_by(Task.priority).all()
            total = sum(count for _, count in distribution)
            result = []
            for priority, count in distribution:
                priority_val = priority.value if hasattr(priority, 'value') else str(priority)
                result.append({
                    'priority': priority_val,
                    'count': count,
                    'percentage': round((count / total * 100), 2) if total > 0 else 0
                })
            logger.info("Task distribution by priority fetched")
            return result
        except Exception as e:
            logger.error(f"Error fetching task distribution by priority: {str(e)}")
            return {'error': f'Error fetching task distribution by priority: {str(e)}'}, 500

    @staticmethod
    def get_project_analytics(project_id=None):
        """Returns analytics for projects (ProjectAnalytics[] format)."""
        try:
            if project_id:
                projects = Project.query.filter_by(id=project_id).all()
            else:
                projects = Project.query.all()

            result = []
            for project in projects:
                total_tasks = len(project.tasks)
                completed_tasks = sum(1 for t in project.tasks if t.status == TaskStatus.DONE)
                completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

                total_hours = db.session.query(func.sum(TimeLog.hours)).join(Task).filter(
                    Task.project_id == project.id
                ).scalar() or 0

                active_sprints = sum(1 for s in project.sprints if s.status.value == 'ACTIVE')

                result.append({
                    'project_id': project.id,
                    'project_name': project.name,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'completion_rate': completion_rate,
                    'total_story_points': 0,
                    'completed_story_points': 0,
                    'total_estimated_hours': project.estimated_hours or 0,
                    'total_actual_hours': float(total_hours),
                    'efficiency_ratio': round(float(project.estimated_hours or 0) / float(total_hours), 2) if total_hours else 0,
                    'team_members_count': len(project.team_members),
                    'sprints_count': len(project.sprints),
                    'active_sprints_count': active_sprints
                })

            logger.info(f"Project analytics fetched for {len(result)} projects")
            return result
        except Exception as e:
            logger.error(f"Error fetching project analytics: {str(e)}")
            return {'error': f'Error fetching project analytics: {str(e)}'}, 500

    @staticmethod
    def get_sprint_analytics(sprint_id):
        """Returns analytics for a sprint."""
        try:
            sprint = Sprint.query.get_or_404(sprint_id)
            tasks = sprint.tasks
            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.DONE)
            completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

            total_hours = db.session.query(func.sum(TimeLog.hours)).join(Task).filter(
                Task.sprint_id == sprint_id
            ).scalar() or 0

            logger.info(f"Sprint analytics fetched for sprint {sprint_id}")
            return {
                'sprint_id': sprint.id,
                'sprint_name': sprint.name,
                'status': sprint.status.value,
                'start_date': sprint.start_date.isoformat() if sprint.start_date else None,
                'end_date': sprint.end_date.isoformat() if sprint.end_date else None,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': completion_rate,
                'total_hours_logged': float(total_hours),
                'project_id': sprint.project_id,
                'project_name': sprint.project.name if sprint.project else None
            }
        except Exception as e:
            logger.error(f"Error fetching sprint analytics for sprint {sprint_id}: {str(e)}")
            return {'error': f'Error fetching sprint analytics: {str(e)}'}, 500

    @staticmethod
    def get_dashboard_analytics(user_id):
        """Returns combined dashboard analytics for a user."""
        try:
            now = datetime.utcnow()
            start_date = now - timedelta(days=30)

            total_tasks = Task.query.filter_by(assigned_to_id=user_id).count()
            completed_tasks = Task.query.filter_by(
                assigned_to_id=user_id, status=TaskStatus.DONE.value
            ).count()
            overdue_tasks = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.due_date.isnot(None),
                Task.due_date < now,
                Task.status != TaskStatus.DONE.value
            ).count()
            in_progress_tasks = Task.query.filter_by(
                assigned_to_id=user_id, status=TaskStatus.IN_PROGRESS.value
            ).count()

            completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

            # Recent activity
            recent_completed = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.status == TaskStatus.DONE.value,
                Task.updated_at >= start_date
            ).count()

            logger.info(f"Dashboard analytics fetched for user {user_id}")
            return {
                'user_id': user_id,
                'period': 'month',
                'start_date': start_date.isoformat(),
                'end_date': now.isoformat(),
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'overdue_tasks': overdue_tasks,
                'completion_rate': completion_rate,
                'recent_completed': recent_completed,
                'task_completion': AnalyticsService.get_task_completion_rate(user_id, 'month'),
                'status_distribution': AnalyticsService.get_task_distribution_by_status(),
                'priority_distribution': AnalyticsService.get_task_distribution_by_priority()
            }
        except Exception as e:
            logger.error(f"Error fetching dashboard analytics for user {user_id}: {str(e)}")
            return {'error': f'Error fetching dashboard analytics: {str(e)}'}, 500

    @staticmethod
    def get_comparison_analytics(user_id):
        """Returns comparison analytics (current period vs previous period)."""
        try:
            now = datetime.utcnow()
            current_start = now - timedelta(days=30)
            previous_start = now - timedelta(days=60)

            current_total = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.created_at >= current_start
            ).count()
            current_completed = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.status == TaskStatus.DONE.value,
                Task.updated_at >= current_start
            ).count()

            previous_total = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.created_at >= previous_start,
                Task.created_at < current_start
            ).count()
            previous_completed = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.status == TaskStatus.DONE.value,
                Task.updated_at >= previous_start,
                Task.updated_at < current_start
            ).count()

            current_rate = round((current_completed / current_total * 100), 2) if current_total > 0 else 0
            previous_rate = round((previous_completed / previous_total * 100), 2) if previous_total > 0 else 0

            logger.info(f"Comparison analytics fetched for user {user_id}")
            return {
                'current_period': {
                    'start_date': current_start.isoformat(),
                    'end_date': now.isoformat(),
                    'total_tasks': current_total,
                    'completed_tasks': current_completed,
                    'completion_rate': current_rate
                },
                'previous_period': {
                    'start_date': previous_start.isoformat(),
                    'end_date': current_start.isoformat(),
                    'total_tasks': previous_total,
                    'completed_tasks': previous_completed,
                    'completion_rate': previous_rate
                },
                'change': {
                    'total_tasks_change': current_total - previous_total,
                    'completed_tasks_change': current_completed - previous_completed,
                    'completion_rate_change': round(current_rate - previous_rate, 2)
                }
            }
        except Exception as e:
            logger.error(f"Error fetching comparison analytics: {str(e)}")
            return {'error': f'Error fetching comparison analytics: {str(e)}'}, 500


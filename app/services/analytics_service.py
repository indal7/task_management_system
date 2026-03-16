# app/services/analytics_service.py
from app.models.task import Task
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint
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

    # ── New enhanced analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_dashboard_summary(user_id):
        """Return a consolidated dashboard metrics object for a user."""
        try:
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)

            # Task counts
            my_tasks_total = Task.query.filter_by(assigned_to_id=user_id).count()
            my_tasks_in_progress = Task.query.filter_by(
                assigned_to_id=user_id, status=TaskStatus.IN_PROGRESS
            ).count()
            my_tasks_done = Task.query.filter_by(
                assigned_to_id=user_id, status=TaskStatus.DONE
            ).count()
            my_tasks_overdue = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.due_date.isnot(None),
                Task.due_date < now,
                Task.status != TaskStatus.DONE,
                Task.status != TaskStatus.CANCELLED,
            ).count()
            my_tasks_this_week = Task.query.filter(
                Task.assigned_to_id == user_id,
                Task.created_at >= week_ago,
            ).count()

            # Projects
            user = User.query.get(user_id)
            projects_owned = len(user.owned_projects) if user else 0
            projects_member = len(user.project_memberships) if user else 0

            # Global totals (useful for admins/managers)
            global_tasks_total = Task.query.count()
            global_tasks_done = Task.query.filter_by(status=TaskStatus.DONE).count()
            global_overdue = Task.query.filter(
                Task.due_date.isnot(None),
                Task.due_date < now,
                Task.status != TaskStatus.DONE,
                Task.status != TaskStatus.CANCELLED,
            ).count()

            return {
                'user_id': user_id,
                'my_tasks': {
                    'total': my_tasks_total,
                    'in_progress': my_tasks_in_progress,
                    'completed': my_tasks_done,
                    'overdue': my_tasks_overdue,
                    'this_week': my_tasks_this_week,
                    'completion_rate': round(
                        my_tasks_done / my_tasks_total, 2
                    ) if my_tasks_total else 0,
                },
                'my_projects': {
                    'owned': projects_owned,
                    'member_of': projects_member,
                    'total': projects_owned + projects_member,
                },
                'global': {
                    'total_tasks': global_tasks_total,
                    'completed_tasks': global_tasks_done,
                    'overdue_tasks': global_overdue,
                    'completion_rate': round(
                        global_tasks_done / global_tasks_total, 2
                    ) if global_tasks_total else 0,
                },
                'generated_at': now.isoformat(),
            }, 200

        except Exception as e:
            logger.error(f"Error fetching dashboard summary for user {user_id}: {e}")
            return {'error': f'Error fetching dashboard summary: {str(e)}'}, 500

    @staticmethod
    def get_project_analytics(project_id):
        """Return analytics for a specific project."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            tasks = project.tasks
            total = len(tasks)
            done = sum(1 for t in tasks if t.status == TaskStatus.DONE)
            in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
            overdue = sum(
                1 for t in tasks
                if t.due_date and t.due_date < datetime.utcnow()
                and t.status not in (TaskStatus.DONE, TaskStatus.CANCELLED)
            )

            # Story points
            total_sp = sum(t.story_points or 0 for t in tasks)
            done_sp = sum(
                t.story_points or 0 for t in tasks
                if t.status == TaskStatus.DONE
            )

            # By priority
            priority_dist = {}
            for p in TaskPriority:
                priority_dist[p.value] = sum(1 for t in tasks if t.priority == p)

            # By status
            status_dist = {}
            for s in TaskStatus:
                status_dist[s.value] = sum(1 for t in tasks if t.status == s)

            # Team
            assignee_ids = {t.assigned_to_id for t in tasks if t.assigned_to_id}
            team_size = len(project.team_members)

            return {
                'project_id': project_id,
                'project_name': project.name,
                'task_summary': {
                    'total': total,
                    'done': done,
                    'in_progress': in_progress,
                    'overdue': overdue,
                    'completion_rate': round(done / total, 2) if total else 0,
                },
                'story_points': {
                    'total': total_sp,
                    'completed': done_sp,
                    'completion_rate': round(done_sp / total_sp, 2) if total_sp else 0,
                },
                'by_priority': priority_dist,
                'by_status': status_dist,
                'team': {
                    'total_members': team_size,
                    'active_contributors': len(assignee_ids),
                },
                'sprints_count': len(project.sprints),
            }, 200

        except Exception as e:
            logger.error(f"Error fetching project analytics for {project_id}: {e}")
            return {'error': f'Error fetching project analytics: {str(e)}'}, 500

    @staticmethod
    def get_sprint_metrics(sprint_id):
        """Return performance metrics for a specific sprint."""
        try:
            sprint = Sprint.query.get(sprint_id)
            if not sprint:
                return {'error': 'Sprint not found'}, 404

            tasks = sprint.tasks
            total = len(tasks)
            done = sum(1 for t in tasks if t.status == TaskStatus.DONE)
            in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)

            total_sp = sum(t.story_points or 0 for t in tasks)
            done_sp = sum(
                t.story_points or 0 for t in tasks
                if t.status == TaskStatus.DONE
            )

            # Duration
            duration_days = None
            if sprint.start_date and sprint.end_date:
                duration_days = (sprint.end_date - sprint.start_date).days

            # Days elapsed / remaining
            now = datetime.utcnow()
            days_elapsed = None
            days_remaining = None
            if sprint.start_date:
                days_elapsed = max((now - sprint.start_date).days, 0)
            if sprint.end_date:
                days_remaining = max((sprint.end_date - now).days, 0)

            return {
                'sprint_id': sprint_id,
                'sprint_name': sprint.name,
                'status': sprint.status.value,
                'task_summary': {
                    'total': total,
                    'done': done,
                    'in_progress': in_progress,
                    'completion_rate': round(done / total, 2) if total else 0,
                },
                'story_points': {
                    'planned': total_sp,
                    'completed': done_sp,
                    'velocity': done_sp,
                    'completion_rate': round(done_sp / total_sp, 2) if total_sp else 0,
                },
                'timeline': {
                    'start_date': sprint.start_date.isoformat() if sprint.start_date else None,
                    'end_date': sprint.end_date.isoformat() if sprint.end_date else None,
                    'duration_days': duration_days,
                    'days_elapsed': days_elapsed,
                    'days_remaining': days_remaining,
                },
                'capacity': {
                    'planned_hours': sprint.capacity_hours,
                    'velocity_points': sprint.velocity_points,
                },
            }, 200

        except Exception as e:
            logger.error(f"Error fetching sprint metrics for {sprint_id}: {e}")
            return {'error': f'Error fetching sprint metrics: {str(e)}'}, 500

    @staticmethod
    def get_team_velocity(project_id=None, num_sprints=5):
        """Calculate team velocity over recent sprints."""
        try:
            query = Sprint.query

            if project_id:
                project = Project.query.get(project_id)
                if not project:
                    return {'error': 'Project not found'}, 404
                query = query.filter_by(project_id=project_id)

            query = query.filter(
                Sprint.status == 'COMPLETED'
            ).order_by(Sprint.end_date.desc()).limit(num_sprints)

            sprints = query.all()
            velocity_data = []

            for sprint in sprints:
                done_sp = sum(
                    t.story_points or 0 for t in sprint.tasks
                    if t.status == TaskStatus.DONE
                )
                velocity_data.append({
                    'sprint_id': sprint.id,
                    'sprint_name': sprint.name,
                    'end_date': sprint.end_date.isoformat() if sprint.end_date else None,
                    'story_points_completed': done_sp,
                    'tasks_completed': sum(
                        1 for t in sprint.tasks if t.status == TaskStatus.DONE
                    ),
                })

            avg_velocity = (
                sum(v['story_points_completed'] for v in velocity_data) / len(velocity_data)
                if velocity_data else 0
            )

            return {
                'project_id': project_id,
                'sprints_analyzed': len(velocity_data),
                'average_velocity': round(avg_velocity, 2),
                'velocity_history': velocity_data,
            }, 200

        except Exception as e:
            logger.error(f"Error fetching team velocity: {e}")
            return {'error': f'Error fetching team velocity: {str(e)}'}, 500


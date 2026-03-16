# app/services/search_service.py
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.models.enums import TaskStatus, TaskPriority, TaskType
from app import db
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger('search')


class SearchService:

    @staticmethod
    def global_search(query_str, user_id, limit=10):
        """Search across tasks, projects, and users."""
        try:
            if not query_str or len(query_str.strip()) < 2:
                return {'error': 'Search query must be at least 2 characters'}, 400

            pattern = f'%{query_str}%'

            # Search tasks
            tasks = Task.query.filter(
                db.or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                )
            ).limit(limit).all()

            # Search projects
            projects = Project.query.filter(
                db.or_(
                    Project.name.ilike(pattern),
                    Project.description.ilike(pattern),
                )
            ).limit(limit).all()

            # Search users (non-sensitive)
            users = User.query.filter(
                User.is_active.is_(True),
                db.or_(
                    User.name.ilike(pattern),
                    User.email.ilike(pattern),
                )
            ).limit(limit).all()

            results = {
                'tasks': [t.to_dict() for t in tasks],
                'projects': [p.to_dict() for p in projects],
                'users': [u.to_dict() for u in users],
                'total': len(tasks) + len(projects) + len(users),
                'query': query_str,
            }
            return results, 200

        except Exception as e:
            logger.error(f'Error in global search: {str(e)}')
            return {'error': f'Error performing search: {str(e)}'}, 500

    @staticmethod
    def advanced_task_search(filters, page=1, per_page=20):
        """Advanced task search with multiple filters."""
        try:
            query = Task.query

            if filters.get('q'):
                pattern = f"%{filters['q']}%"
                query = query.filter(
                    db.or_(
                        Task.title.ilike(pattern),
                        Task.description.ilike(pattern),
                        Task.acceptance_criteria.ilike(pattern),
                    )
                )

            if filters.get('project_id'):
                query = query.filter(Task.project_id == filters['project_id'])

            if filters.get('sprint_id'):
                query = query.filter(Task.sprint_id == filters['sprint_id'])

            if filters.get('assigned_to_id'):
                query = query.filter(Task.assigned_to_id == filters['assigned_to_id'])

            if filters.get('created_by_id'):
                query = query.filter(Task.created_by_id == filters['created_by_id'])

            if filters.get('status'):
                statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
                valid = []
                for s in statuses:
                    try:
                        valid.append(TaskStatus[s.upper()])
                    except KeyError:
                        pass
                if valid:
                    query = query.filter(Task.status.in_(valid))

            if filters.get('priority'):
                priorities = filters['priority'] if isinstance(filters['priority'], list) else [filters['priority']]
                valid = []
                for p in priorities:
                    try:
                        valid.append(TaskPriority[p.upper()])
                    except KeyError:
                        pass
                if valid:
                    query = query.filter(Task.priority.in_(valid))

            if filters.get('task_type'):
                types = filters['task_type'] if isinstance(filters['task_type'], list) else [filters['task_type']]
                valid = []
                for t in types:
                    try:
                        valid.append(TaskType[t.upper()])
                    except KeyError:
                        pass
                if valid:
                    query = query.filter(Task.task_type.in_(valid))

            if filters.get('due_date_from'):
                try:
                    query = query.filter(Task.due_date >= datetime.fromisoformat(filters['due_date_from']))
                except (ValueError, TypeError):
                    pass

            if filters.get('due_date_to'):
                try:
                    query = query.filter(Task.due_date <= datetime.fromisoformat(filters['due_date_to']))
                except (ValueError, TypeError):
                    pass

            if filters.get('overdue') in (True, 'true', '1'):
                query = query.filter(
                    Task.due_date < datetime.utcnow(),
                    Task.status != TaskStatus.DONE,
                    Task.status != TaskStatus.CANCELLED,
                )

            total = query.count()
            tasks = query.order_by(Task.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

            return {
                'tasks': [t.to_dict() for t in tasks],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
            }, 200

        except Exception as e:
            logger.error(f'Error in advanced task search: {str(e)}')
            return {'error': f'Error searching tasks: {str(e)}'}, 500

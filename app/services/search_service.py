# app/services/search_service.py
from app.models.task import Task
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.user import User
from app.models.enums import TaskStatus, TaskPriority, TaskType
from app import db
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger('search')


class SearchService:

    @staticmethod
    def _get_accessible_project_ids(user):
        if not user:
            return []

        project_ids = {project.id for project in getattr(user, 'owned_projects', [])}

        for membership in getattr(user, 'project_memberships', []):
            project = getattr(membership, 'project', None)
            if project is not None and getattr(project, 'id', None) is not None:
                project_ids.add(project.id)

        return list(project_ids)

    @staticmethod
    def _build_search_pattern(query_str):
        return f"%{query_str.strip()}%"

    @staticmethod
    def global_search(query_str, user_id, limit=10):
        """Search across tasks, projects, sprints, and users."""
        try:
            if not query_str or len(query_str.strip()) < 2:
                return {'error': 'Search query must be at least 2 characters'}, 400

            user = User.query.get_or_404(user_id)
            pattern = SearchService._build_search_pattern(query_str)
            accessible_project_ids = SearchService._get_accessible_project_ids(user)

            task_query = Task.query.filter(
                db.or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                    Task.acceptance_criteria.ilike(pattern),
                    db.cast(Task.id, db.String).ilike(pattern),
                    db.cast(Task.project_id, db.String).ilike(pattern),
                    db.cast(Task.sprint_id, db.String).ilike(pattern)
                )
            )

            if accessible_project_ids:
                task_query = task_query.filter(
                    db.or_(
                        Task.project_id.in_(accessible_project_ids),
                        Task.assigned_to_id == user_id,
                        Task.created_by_id == user_id,
                        Task.project_id.is_(None)
                    )
                )
            else:
                task_query = task_query.filter(
                    db.or_(
                        Task.assigned_to_id == user_id,
                        Task.created_by_id == user_id,
                        Task.project_id.is_(None)
                    )
                )

            tasks = task_query.order_by(Task.updated_at.desc()).limit(limit).all()

            project_query = Project.query.filter(
                db.or_(
                    Project.name.ilike(pattern),
                    Project.description.ilike(pattern),
                    Project.client_name.ilike(pattern),
                    Project.client_email.ilike(pattern),
                    Project.repository_url.ilike(pattern),
                    Project.documentation_url.ilike(pattern),
                    db.cast(Project.id, db.String).ilike(pattern)
                )
            )

            if accessible_project_ids:
                project_query = project_query.filter(Project.id.in_(accessible_project_ids))
            else:
                project_query = project_query.filter(Project.owner_id == user_id)

            projects = project_query.order_by(Project.updated_at.desc()).limit(limit).all()

            sprint_query = Sprint.query.join(Project, Sprint.project_id == Project.id).filter(
                db.or_(
                    Sprint.name.ilike(pattern),
                    Sprint.description.ilike(pattern),
                    Sprint.goal.ilike(pattern),
                    db.cast(Sprint.id, db.String).ilike(pattern),
                    db.cast(Sprint.project_id, db.String).ilike(pattern),
                    Project.name.ilike(pattern)
                )
            )

            if accessible_project_ids:
                sprint_query = sprint_query.filter(Sprint.project_id.in_(accessible_project_ids))
            else:
                sprint_query = sprint_query.filter(Project.owner_id == user_id)

            sprints = sprint_query.order_by(Sprint.updated_at.desc()).limit(limit).all()

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
                'sprints': [s.to_dict() for s in sprints],
                'users': [u.to_dict() for u in users],
                'total': len(tasks) + len(projects) + len(sprints) + len(users),
                'query': query_str,
            }
            return results, 200

        except Exception as e:
            logger.error(f'Error in global search: {str(e)}')
            return {'error': f'Error performing search: {str(e)}'}, 500

    @staticmethod
    def advanced_task_search(filters, user_id, page=1, per_page=20):
        """Advanced task search with multiple filters."""
        try:
            user = User.query.get_or_404(user_id)
            accessible_project_ids = SearchService._get_accessible_project_ids(user)
            query = Task.query

            if accessible_project_ids:
                query = query.filter(
                    db.or_(
                        Task.project_id.in_(accessible_project_ids),
                        Task.assigned_to_id == user_id,
                        Task.created_by_id == user_id,
                        Task.project_id.is_(None)
                    )
                )
            else:
                query = query.filter(
                    db.or_(
                        Task.assigned_to_id == user_id,
                        Task.created_by_id == user_id,
                        Task.project_id.is_(None)
                    )
                )

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

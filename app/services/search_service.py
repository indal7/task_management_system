# app/services/search_service.py
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.models.sprint import Sprint
from app import db
from app.utils.logger import get_logger
import json

logger = get_logger('search_service')


class SearchService:

    @staticmethod
    def global_search(query_str, user_id, entity_types=None, limit=10):
        """
        Global search across tasks, projects, users, and sprints.

        Returns a dict with separate lists for each entity type.
        """
        try:
            types = entity_types or ['tasks', 'projects', 'users', 'sprints']
            like = f"%{query_str}%"
            results = {}

            if 'tasks' in types:
                tasks = Task.query.filter(
                    db.or_(
                        Task.title.ilike(like),
                        Task.description.ilike(like),
                    )
                ).limit(limit).all()
                results['tasks'] = [t.to_dict() for t in tasks]

            if 'projects' in types:
                projects = Project.query.filter(
                    db.or_(
                        Project.name.ilike(like),
                        Project.description.ilike(like),
                    )
                ).limit(limit).all()
                results['projects'] = [p.to_dict() for p in projects]

            if 'users' in types:
                users = User.query.filter(
                    User.is_active == True,  # noqa: E712
                    db.or_(
                        User.name.ilike(like),
                        User.email.ilike(like),
                    )
                ).limit(limit).all()
                results['users'] = [u.to_dict() for u in users]

            if 'sprints' in types:
                sprints = Sprint.query.filter(
                    db.or_(
                        Sprint.name.ilike(like),
                        Sprint.goal.ilike(like),
                    )
                ).limit(limit).all()
                results['sprints'] = [s.to_dict() for s in sprints]

            results['query'] = query_str
            results['total'] = sum(
                len(v) for v in results.values() if isinstance(v, list)
            )
            return results, 200

        except Exception as e:
            logger.error(f"Global search error: {e}")
            return {'error': f'Search error: {str(e)}'}, 500

    @staticmethod
    def advanced_task_search(user_id, filters, page=1, per_page=20,
                             sort_by='created_at', sort_order='desc'):
        """
        Advanced task search with complex filters.

        Supported filters:
        - q: full-text keyword (title / description)
        - status: single or comma-separated list
        - priority: single or comma-separated list
        - task_type: single or comma-separated list
        - project_id: integer
        - sprint_id: integer
        - assigned_to_id: integer
        - created_by_id: integer
        - labels: comma-separated label strings
        - due_before: ISO date string
        - due_after: ISO date string
        - overdue: boolean
        """
        try:
            from datetime import datetime
            from app.models.enums import TaskStatus, TaskPriority, TaskType

            query = Task.query

            # Keyword search
            if filters.get('q'):
                like = f"%{filters['q']}%"
                query = query.filter(
                    db.or_(Task.title.ilike(like), Task.description.ilike(like))
                )

            # Status filter (single or list)
            if filters.get('status'):
                statuses = [s.strip().upper() for s in
                            str(filters['status']).split(',')]
                try:
                    status_enums = [TaskStatus[s] for s in statuses]
                    query = query.filter(Task.status.in_(status_enums))
                except KeyError as ke:
                    return {'error': f'Invalid status: {ke}'}, 400

            # Priority filter
            if filters.get('priority'):
                priorities = [p.strip().upper() for p in
                              str(filters['priority']).split(',')]
                try:
                    priority_enums = [TaskPriority[p] for p in priorities]
                    query = query.filter(Task.priority.in_(priority_enums))
                except KeyError as ke:
                    return {'error': f'Invalid priority: {ke}'}, 400

            # Task type filter
            if filters.get('task_type'):
                types = [t.strip().upper() for t in
                         str(filters['task_type']).split(',')]
                try:
                    type_enums = [TaskType[t] for t in types]
                    query = query.filter(Task.task_type.in_(type_enums))
                except KeyError as ke:
                    return {'error': f'Invalid task_type: {ke}'}, 400

            # Relationship filters
            for field in ['project_id', 'sprint_id', 'assigned_to_id', 'created_by_id']:
                if filters.get(field):
                    query = query.filter(
                        getattr(Task, field) == int(filters[field])
                    )

            # Label search (stored as JSON in text field)
            if filters.get('labels'):
                labels = [label.strip() for label in str(filters['labels']).split(',')]
                for label in labels:
                    query = query.filter(Task.labels.ilike(f'%{label}%'))

            # Date filters
            if filters.get('due_before'):
                try:
                    due_before = datetime.fromisoformat(filters['due_before'])
                    query = query.filter(Task.due_date <= due_before)
                except ValueError:
                    return {'error': 'Invalid due_before date format'}, 400

            if filters.get('due_after'):
                try:
                    due_after = datetime.fromisoformat(filters['due_after'])
                    query = query.filter(Task.due_date >= due_after)
                except ValueError:
                    return {'error': 'Invalid due_after date format'}, 400

            if filters.get('overdue') in (True, 'true', '1'):
                query = query.filter(
                    Task.due_date.isnot(None),
                    Task.due_date < datetime.utcnow(),
                    Task.status != TaskStatus.DONE,
                    Task.status != TaskStatus.CANCELLED,
                )

            # Sorting
            sort_col = getattr(Task, sort_by, Task.created_at)
            if sort_order == 'asc':
                query = query.order_by(sort_col.asc())
            else:
                query = query.order_by(sort_col.desc())

            total = query.count()
            tasks = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'data': [t.to_dict() for t in tasks],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
                'has_next': page * per_page < total,
                'has_prev': page > 1,
                'filters_applied': {k: v for k, v in filters.items() if v},
            }, 200

        except Exception as e:
            logger.error(f"Advanced task search error: {e}")
            return {'error': f'Search error: {str(e)}'}, 500

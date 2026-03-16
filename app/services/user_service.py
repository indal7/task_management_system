# app/services/user_service.py
from app.models.user import User
from app.models.task import Task
from app.models.enums import UserRole, TaskStatus
from app import db
from app.utils.logger import get_logger
from app.utils.cache_utils import cache, invalidate_user_cache
from sqlalchemy import func

logger = get_logger('user_service')


class UserService:

    @staticmethod
    def get_users(page=1, per_page=20, search=None, role=None,
                  is_active=None, sort_by='created_at', sort_order='desc'):
        """List users with pagination, search, and filtering."""
        try:
            query = User.query

            if search:
                like = f"%{search}%"
                query = query.filter(
                    db.or_(User.name.ilike(like), User.email.ilike(like))
                )

            if role:
                try:
                    role_enum = UserRole[role.upper()]
                    query = query.filter(User.role == role_enum)
                except KeyError:
                    return {'error': f'Invalid role: {role}'}, 400

            if is_active is not None:
                query = query.filter(User.is_active == is_active)

            # Sorting
            sort_col = getattr(User, sort_by, User.created_at)
            if sort_order == 'asc':
                query = query.order_by(sort_col.asc())
            else:
                query = query.order_by(sort_col.desc())

            total = query.count()
            users = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'data': [u.to_dict() for u in users],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
                'has_next': page * per_page < total,
                'has_prev': page > 1,
            }, 200

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return {'error': f'Error fetching users: {str(e)}'}, 500

    @staticmethod
    def get_user_by_id(user_id, include_stats=False):
        """Get a single user profile, optionally with activity stats."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            data = user.to_dict(include_sensitive=True)

            if include_stats:
                total_tasks = Task.query.filter_by(assigned_to_id=user_id).count()
                completed = Task.query.filter_by(
                    assigned_to_id=user_id, status=TaskStatus.DONE
                ).count()
                in_progress = Task.query.filter(
                    Task.assigned_to_id == user_id,
                    Task.status == TaskStatus.IN_PROGRESS
                ).count()
                created = Task.query.filter_by(created_by_id=user_id).count()
                projects_count = len(user.owned_projects) + len(user.project_memberships)

                data['stats'] = {
                    'total_assigned_tasks': total_tasks,
                    'completed_tasks': completed,
                    'in_progress_tasks': in_progress,
                    'tasks_created': created,
                    'projects_count': projects_count,
                    'completion_rate': round(completed / total_tasks, 2) if total_tasks else 0,
                }

            return data, 200

        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return {'error': f'Error fetching user: {str(e)}'}, 500

    @staticmethod
    def update_user(user_id, data, requesting_user_id, requesting_user_role):
        """Update user info. Admins can update any field including role."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            # Only admin or the user themselves can update
            is_admin = requesting_user_role == UserRole.ADMIN
            is_self = int(requesting_user_id) == int(user_id)

            if not is_admin and not is_self:
                return {'error': 'Permission denied'}, 403

            # Fields allowed for self-update
            allowed_fields = [
                'name', 'bio', 'skills', 'github_username',
                'linkedin_url', 'phone', 'timezone', 'daily_work_hours',
                'hourly_rate', 'avatar_url',
            ]

            # Admin can also change role and is_active
            if is_admin:
                allowed_fields += ['role', 'is_active', 'email']

            for field in allowed_fields:
                if field in data:
                    if field == 'role':
                        try:
                            setattr(user, field, UserRole[data[field].upper()])
                        except KeyError:
                            return {'error': f'Invalid role: {data[field]}'}, 400
                    elif field == 'email':
                        # Check email uniqueness
                        existing = User.query.filter(
                            User.email == data['email'],
                            User.id != user_id
                        ).first()
                        if existing:
                            return {'error': 'Email already in use'}, 400
                        user.email = data['email']
                    else:
                        setattr(user, field, data[field])

            db.session.commit()
            invalidate_user_cache(user_id)
            cache.delete('all_users_list')

            logger.info(f"User {user_id} updated by {requesting_user_id}")
            return user.to_dict(include_sensitive=True), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            return {'error': f'Error updating user: {str(e)}'}, 500

    @staticmethod
    def delete_user(user_id, requesting_user_id, requesting_user_role):
        """Delete/deactivate a user (admin only)."""
        try:
            if requesting_user_role != UserRole.ADMIN:
                return {'error': 'Admin access required'}, 403

            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            if int(user_id) == int(requesting_user_id):
                return {'error': 'Cannot delete your own account'}, 400

            # Soft delete – deactivate instead of hard delete to preserve data integrity
            user.is_active = False
            db.session.commit()

            invalidate_user_cache(user_id)
            cache.delete('all_users_list')

            logger.info(f"User {user_id} deactivated by admin {requesting_user_id}")
            return {'message': 'User deactivated successfully'}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            return {'error': f'Error deleting user: {str(e)}'}, 500

    @staticmethod
    def search_users(query_str, limit=10):
        """Quick user search by name or email (for autocomplete)."""
        try:
            like = f"%{query_str}%"
            users = User.query.filter(
                User.is_active == True,  # noqa: E712
                db.or_(User.name.ilike(like), User.email.ilike(like))
            ).limit(limit).all()

            return [
                {'id': u.id, 'name': u.name, 'email': u.email,
                 'role': u.role.value, 'avatar_url': u.avatar_url}
                for u in users
            ], 200

        except Exception as e:
            logger.error(f"User search error: {e}")
            return {'error': f'Search error: {str(e)}'}, 500

    @staticmethod
    def bulk_update_users(user_ids, updates, requesting_user_role):
        """Bulk update multiple users (admin only)."""
        try:
            if requesting_user_role != UserRole.ADMIN:
                return {'error': 'Admin access required'}, 403

            users = User.query.filter(User.id.in_(user_ids)).all()
            updated = []

            for user in users:
                if 'is_active' in updates:
                    user.is_active = updates['is_active']
                if 'role' in updates:
                    try:
                        user.role = UserRole[updates['role'].upper()]
                    except KeyError:
                        return {'error': f"Invalid role: {updates['role']}"}, 400
                updated.append(user.id)

            db.session.commit()

            for uid in updated:
                invalidate_user_cache(uid)
            cache.delete('all_users_list')

            logger.info(f"Bulk updated {len(updated)} users")
            return {'updated_count': len(updated), 'updated_ids': updated}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk user update error: {e}")
            return {'error': f'Bulk update error: {str(e)}'}, 500

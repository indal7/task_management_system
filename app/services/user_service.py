# app/services/user_service.py
from app.models.user import User
from app.models.task import Task
from app.models.enums import UserRole, TaskStatus
from app import db
from app.utils.logger import get_logger

logger = get_logger('users')


class UserService:

    @staticmethod
    def list_users(page=1, per_page=20, search=None, role=None, is_active=None):
        """List users with optional filtering and pagination."""
        try:
            query = User.query

            if search:
                pattern = f'%{search}%'
                query = query.filter(
                    db.or_(
                        User.name.ilike(pattern),
                        User.email.ilike(pattern)
                    )
                )

            if role:
                try:
                    role_enum = UserRole[role.upper()]
                    query = query.filter(User.role == role_enum)
                except KeyError:
                    return {'error': f'Invalid role: {role}'}, 400

            if is_active is not None:
                query = query.filter(User.is_active == is_active)

            total = query.count()
            users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

            return {
                'users': [u.to_dict() for u in users],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
            }, 200

        except Exception as e:
            logger.error(f'Error listing users: {str(e)}')
            return {'error': f'Error listing users: {str(e)}'}, 500

    @staticmethod
    def get_user(user_id):
        """Get a specific user with statistics."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            # Gather statistics
            total_assigned = Task.query.filter_by(assigned_to_id=user_id).count()
            completed = Task.query.filter_by(
                assigned_to_id=user_id, status=TaskStatus.DONE
            ).count()

            result = user.to_dict()
            result['stats'] = {
                'total_assigned_tasks': total_assigned,
                'completed_tasks': completed,
                'completion_rate': round(completed / total_assigned, 2) if total_assigned else 0,
                'projects_count': len(user.owned_projects) + len(user.project_memberships),
            }
            return result, 200

        except Exception as e:
            logger.error(f'Error getting user {user_id}: {str(e)}')
            return {'error': f'Error fetching user: {str(e)}'}, 500

    @staticmethod
    def update_user(user_id, data, requesting_user_id):
        """Update user information."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            requesting_user = User.query.get(requesting_user_id)
            # Only the user themselves or an admin may update
            if int(user_id) != int(requesting_user_id) and (not requesting_user or requesting_user.role != UserRole.ADMIN):
                return {'error': 'Permission denied'}, 403

            allowed_fields = [
                'name', 'bio', 'skills', 'github_username', 'linkedin_url',
                'phone', 'timezone', 'daily_work_hours', 'hourly_rate', 'avatar_url'
            ]
            for field in allowed_fields:
                if field in data:
                    setattr(user, field, data[field])

            # Only admins can change email or role
            if requesting_user and requesting_user.role == UserRole.ADMIN:
                if 'email' in data:
                    existing = User.query.filter(
                        User.email == data['email'], User.id != user_id
                    ).first()
                    if existing:
                        return {'error': 'Email already in use'}, 400
                    user.email = data['email']
                if 'role' in data:
                    try:
                        user.role = UserRole[data['role'].upper()]
                    except KeyError:
                        return {'error': f"Invalid role: {data['role']}"}, 400

            db.session.commit()
            logger.info(f'User {user_id} updated by {requesting_user_id}')
            return user.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error updating user {user_id}: {str(e)}')
            return {'error': f'Error updating user: {str(e)}'}, 500

    @staticmethod
    def delete_user(user_id, requesting_user_id):
        """Soft-delete a user (deactivate). Admin only."""
        try:
            requesting_user = User.query.get(requesting_user_id)
            if not requesting_user or requesting_user.role != UserRole.ADMIN:
                return {'error': 'Admin access required'}, 403

            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            if user_id == requesting_user_id:
                return {'error': 'Cannot delete your own account'}, 400

            user.is_active = False
            db.session.commit()
            logger.info(f'User {user_id} deactivated by admin {requesting_user_id}')
            return {'message': 'User deactivated successfully'}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error deleting user {user_id}: {str(e)}')
            return {'error': f'Error deleting user: {str(e)}'}, 500

    @staticmethod
    def activate_user(user_id, requesting_user_id):
        """Activate a user account. Admin only."""
        try:
            requesting_user = User.query.get(requesting_user_id)
            if not requesting_user or requesting_user.role != UserRole.ADMIN:
                return {'error': 'Admin access required'}, 403

            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            user.is_active = True
            db.session.commit()
            return {'message': 'User activated successfully'}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error activating user {user_id}: {str(e)}')
            return {'error': f'Error activating user: {str(e)}'}, 500

    @staticmethod
    def search_users(query_str, limit=10):
        """Search users by name or email."""
        try:
            pattern = f'%{query_str}%'
            users = User.query.filter(
                User.is_active == True,
                db.or_(User.name.ilike(pattern), User.email.ilike(pattern))
            ).limit(limit).all()
            return [u.to_dict() for u in users], 200

        except Exception as e:
            logger.error(f'Error searching users: {str(e)}')
            return {'error': f'Error searching users: {str(e)}'}, 500

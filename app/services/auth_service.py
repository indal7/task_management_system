# app/services/auth_service.py
from app.models.user import User
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)
from app import db
from werkzeug.security import generate_password_hash
from app.models.enums import UserRole
from app.utils.cache_utils import cache, cached_per_user, CacheKeys, invalidate_user_cache, invalidate_project_cache
from app.utils.logger import get_logger, log_db_query

logger = get_logger('auth')


class AuthService:

    @staticmethod
    def register_user(username, email, password, role="user"):
        """Registers a new user."""
        try:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                logger.warning(f"Attempt to register existing email: {email}")
                return {"error": "User with this email already exists"}, 400

            hashed_password = generate_password_hash(password)
            try:
                user_role = UserRole[role.upper()]
            except KeyError:
                return {"error": "Invalid role"}, 400

            user = User(name=username, email=email, role=user_role, password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
            log_db_query("INSERT", "users")
            logger.info(f"User {user.id} registered successfully")

            # Invalidate global user cache
            invalidate_user_cache(user.id)

            return {"message": "User registered successfully", "user": user.to_dict()}, 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user {email}: {str(e)}")
            return {"error": f"Error registering user: {str(e)}"}, 500

    @staticmethod
    def login_user(email, password):
        """Authenticates user and returns tokens."""
        try:
            user = User.query.filter_by(email=email).first()

            if not user:
                logger.warning(f"Login attempt failed. User not found: {email}")
                return {"success": False, "error": "User not found, please register first"}, 404

            if not user.check_password(password):
                logger.warning(f"Login attempt failed. Invalid password for user: {email}")
                return {"success": False, "error": "Invalid credentials"}, 401

            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))

            logger.info(f"User {user.id} logged in successfully")
            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.to_dict()
            }

        except Exception as e:
            logger.error(f"Error logging in user {email}: {str(e)}")
            return {"error": f"Error logging in user: {str(e)}"}, 500

    @staticmethod
    @jwt_required()
    def validate_token():
        """Validates the JWT access token and returns the user details."""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get_or_404(current_user_id)
            logger.info(f"Token validated for user {user.id}")
            return user.to_dict()
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return {"error": f"Token validation failed: {str(e)}"}, 401

    @staticmethod
    def change_password(user_id, new_password):
        """Changes the user's password."""
        try:
            user = User.query.get_or_404(user_id)
            user.set_password(new_password)
            db.session.commit()
            log_db_query("UPDATE", "users")
            logger.info(f"Password changed for user {user.id}")

            # Invalidate user cache
            invalidate_user_cache(user.id)

            return user.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing password for user {user_id}: {str(e)}")
            return {"error": f"Error changing password: {str(e)}"}, 500

    @staticmethod
    @jwt_required(refresh=True)
    def refresh_token():
        """Generates a new access token using a valid refresh token."""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get_or_404(current_user_id)
            logger.info(f"Access token refreshed for user {user.id}")
            return {
                "access_token": create_access_token(identity=str(user.id)),
                "user": user.to_dict()
            }
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return {"error": f"Error refreshing token: {str(e)}"}, 500

    @staticmethod
    @jwt_required()
    def update_profile(user_id, data):
        """Updates the user's profile."""
        try:
            user = User.query.get_or_404(user_id)

            if 'password' in data:
                user.password_hash = generate_password_hash(data['password'])

            if 'email' in data:
                user.email = data['email']

            if 'name' in data:
                user.name = data['name']

            db.session.commit()
            log_db_query("UPDATE", "users")
            logger.info(f"User {user.id} profile updated")

            # Invalidate user cache
            invalidate_user_cache(user.id)

            return {'message': 'Profile updated successfully'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile for user {user_id}: {str(e)}")
            return {'error': f'Error updating profile: {str(e)}'}, 400

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.USERS)
    def get_all_users_ids_and_names():
        """Fetches all users' ids and names."""
        try:
            users = User.get_all_user_ids_and_names()
            logger.info(f"Fetched {len(users)} users")
            logger.info(f"type of users: {type(users)}")
            return users
        except Exception as e:
            logger.error(f"Failed to fetch users: {str(e)}")
            return {'error': f'Failed to fetch users: {str(e)}'}, 500

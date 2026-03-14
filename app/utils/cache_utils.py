"""
Caching utilities for the Task Management System
"""
from flask_caching import Cache
from functools import wraps
from flask_jwt_extended import get_jwt_identity
import json
import hashlib
import os

# Initialize cache (will be configured in __init__.py)
cache = Cache()

def init_cache(app):
    """Initialize caching with the Flask app"""
    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/0"
    cache.init_app(app)
    return cache

# Cache key generators
def make_cache_key(*args, **kwargs):
    """Generate cache key from arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def user_cache_key(prefix="", user_id=None, **kwargs):
    """
    Generate cache key for a user.
    - If user_id is provided, use it
    - Otherwise try JWT
    """
    if user_id is None:
        try:
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
        except RuntimeError:
            # JWT not present
            user_id = 'anonymous'

    base_key = f"{prefix}:user_{user_id}"
    if kwargs:
        params = "|".join([f"{k}={v}" for k, v in sorted(kwargs.items())])
        base_key += f":{hashlib.md5(params.encode()).hexdigest()}"
    return base_key


# Custom cache decorators
def cached_per_user(timeout=300, key_prefix=""):
    """Cache decorator that includes user_id in key"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = user_cache_key(key_prefix or f.__name__, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                try:
                    return json.loads(cached_result)
                except Exception:
                    return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            try:
                cache.set(cache_key, json.dumps(result), timeout=timeout)
            except TypeError:
                # Fallback if object is not JSON serializable
                cache.set(cache_key, result, timeout=timeout)
            return result
        return decorated_function
    return decorator

# Safe cache invalidation using scan_iter
def invalidate_user_cache(user_id, pattern="*"):
    """Invalidate all cache entries for a user"""
    try:
        client = cache.cache._client
        deleted = 0
        for key in client.scan_iter(f"*user_{user_id}*{pattern}*"):
            client.delete(key)
            deleted += 1
        if deleted > 0:
            print(f"🗑️ Invalidated {deleted} cache entries for user {user_id}")
    except Exception as e:
        print(f"⚠️ Cache invalidation failed: {e}")

def invalidate_project_cache(project_id):
    """Invalidate all cache entries related to a project"""
    try:
        client = cache.cache._client
        deleted = 0
        for key in client.scan_iter(f"*project_{project_id}*"):
            client.delete(key)
            deleted += 1
        if deleted > 0:
            print(f"🗑️ Invalidated {deleted} cache entries for project {project_id}")
    except Exception as e:
        print(f"⚠️ Cache invalidation failed: {e}")

# Common cache patterns
class CacheKeys:
    USER_TASKS = "user_tasks"
    USER_PROJECTS = "user_projects"
    PROJECT_TASKS = "project_tasks"
    PROJECT_MEMBERS = "project_members"
    SPRINT_TASKS = "sprint_tasks"
    USER_NOTIFICATIONS = "user_notifications"
    DASHBOARD_DATA = "dashboard_data"
    ANALYTICS_DATA = "analytics_data"
    USER_COMMENTS = "user_comments"
    USER_ATTACHMENTS = "user_attachments"
    USERS = "users"
    ROLES = "roles"
    PERMISSIONS = "permissions"
    SETTINGS = "settings"
    USER_SPRINTS = "user_sprints"
    USER_ANALYTICS = "user_analytics"
    USER_COMMENTS = "user_comments"
    TASK_COMMENTS = "task_comments"
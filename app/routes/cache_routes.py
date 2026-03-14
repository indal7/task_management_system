"""
Cache management routes (for development/admin)
"""
from flask import Blueprint
from app.utils.cache_utils import cache
from app.utils.decorators import admin_required
from flask_jwt_extended import jwt_required

cache_bp = Blueprint('cache', __name__)

@cache_bp.route('/clear', methods=['POST'])
@jwt_required()
@admin_required
def clear_cache():
    """Clear all cache entries"""
    cache.clear()
    return {'success': True, 'message': 'Cache cleared successfully'}

@cache_bp.route('/stats', methods=['GET'])
@jwt_required() 
@admin_required
def cache_stats():
    """Get cache statistics"""
    try:
        # This works with Redis
        info = cache.cache._write_client.info()
        return {
            'success': True,
            'data': {
                'connected_clients': info.get('connected_clients'),
                'used_memory': info.get('used_memory_human'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
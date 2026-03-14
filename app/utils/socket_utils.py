# app/utils/socket_utils.py
"""
Socket.IO utilities for real-time communication
"""
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token
from functools import wraps
import json
from datetime import datetime
import logging

# Initialize SocketIO (configured in __init__.py)
socketio = None
connected_users = {}  # sid -> user_id

# Configure logger
logger = logging.getLogger('socketio')
if not logger.handlers:
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    register_socket_events()
    logger.info("SocketIO initialized")
    return socketio


def authenticated_only(f):
    """Decorator to ensure user is connected and authenticated via SocketIO"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = connected_users.get(request.sid)
        if not user_id:
            emit('error', {'message': 'Authentication required'})
            disconnect()
            logger.warning(f"Unauthorized access attempt from SID {request.sid}")
            return
        kwargs['user_id'] = user_id
        return f(*args, **kwargs)
    return decorated


def register_socket_events():
    """Register all Socket.IO event handlers"""

    @socketio.on('connect')
    def handle_connect(auth=None):
        """Handle client connection"""
        try:
            token = None
            if auth and isinstance(auth, dict):
                token = auth.get('token')
            if not token:
                token = request.args.get('token')

            if not token:
                emit('error', {'message': 'Authentication required'})
                disconnect()
                logger.warning(f"Connection rejected: No token provided for SID {request.sid}")
                return

            decoded_token = decode_token(token)
            user_id = decoded_token['sub']

            connected_users[request.sid] = user_id
            join_room(f"user_{user_id}")

            from app.models.user import User
            user = User.query.get(user_id)
            if user:
                emit('connected', {
                    'message': f'Welcome {user.email}!',
                    'user_id': user_id,
                    'room': f"user_{user_id}"
                })
                logger.info(f"User {user.email} (ID: {user_id}) connected with SID {request.sid}")
            else:
                emit('error', {'message': 'User not found'})
                disconnect()
                logger.warning(f"Connection rejected: User ID {user_id} not found")

        except Exception as e:
            emit('error', {'message': 'Authentication failed'})
            disconnect()
            logger.error(f"Authentication error for SID {request.sid}: {e}", exc_info=True)


    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        user_id = connected_users.pop(request.sid, None)
        logger.info(f"Client disconnected: SID {request.sid}, User ID {user_id}")


    @socketio.on('join_user_room')
    @authenticated_only
    def handle_join_user_room(data, user_id):
        room = f"user_{user_id}"
        join_room(room)
        emit('room_joined', {'room': room, 'message': 'Joined personal notification room'})
        logger.info(f"User {user_id} joined personal room: {room}")


    @socketio.on('join_project_room')
    @authenticated_only
    def handle_join_project_room(data, user_id):
        try:
            project_id = data.get('project_id')
            if not project_id:
                emit('error', {'message': 'Project ID required'})
                return

            # TODO: verify user access to project
            room = f"project_{project_id}"
            join_room(room)
            emit('room_joined', {'room': room, 'message': f'Joined project {project_id} room'})
            logger.info(f"User {user_id} joined project room: {room}")

        except Exception as e:
            emit('error', {'message': f'Failed to join project room: {str(e)}'})
            logger.error(f"Error joining project room: {e}", exc_info=True)


    @socketio.on('get_notifications')
    @authenticated_only
    def handle_get_notifications(data, user_id):
        try:
            from app.models.notification import Notification

            unread_only = data.get('unread_only', False)
            query = Notification.query.filter_by(user_id=user_id)
            if unread_only:
                query = query.filter_by(read=False)

            notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
            emit('notifications_data', {
                'notifications': [n.to_dict() for n in notifications],
                'total': len(notifications),
                'unread_count': Notification.get_unread_count(user_id)
            })
            logger.info(f"Sent {len(notifications)} notifications to user {user_id}")

        except Exception as e:
            emit('error', {'message': f'Failed to get notifications: {str(e)}'})
            logger.error(f"Error fetching notifications for user {user_id}: {e}", exc_info=True)


    @socketio.on('mark_notification_read')
    @authenticated_only
    def handle_mark_notification_read(data, user_id):
        try:
            from app.models.notification import Notification

            notification_id = data.get('notification_id')
            if not notification_id:
                emit('error', {'message': 'Notification ID required'})
                return

            notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
            if not notification:
                emit('error', {'message': 'Notification not found'})
                return

            notification.mark_as_read()
            emit('notification_updated', {
                'notification_id': notification_id,
                'status': 'read',
                'unread_count': Notification.get_unread_count(user_id)
            })
            logger.info(f"Notification {notification_id} marked as read by user {user_id}")

        except Exception as e:
            emit('error', {'message': f'Failed to mark notification as read: {str(e)}'})
            logger.error(f"Error marking notification as read for user {user_id}: {e}", exc_info=True)


    @socketio.on('ping')
    def handle_ping(data):
        emit('pong', {'message': 'Server is alive', 'timestamp': str(datetime.utcnow())})
        logger.debug(f"Ping received from SID {request.sid}")


# ---------------- Utility functions for broadcasting ---------------- #

def broadcast_notification(user_id, notification_data):
    """Broadcast a notification to a specific user"""
    if socketio:
        socketio.emit('new_notification', notification_data, room=f"user_{user_id}")
        logger.info(f"Notification sent to user {user_id}: {notification_data.get('title', 'No title')}")


def broadcast_to_project(project_id, event_name, data):
    """Broadcast an event to all users in a project room"""
    if socketio:
        socketio.emit(event_name, data, room=f"project_{project_id}")
        logger.info(f"Broadcast to project {project_id}: {event_name}")


def broadcast_task_update(task_data, project_id=None, assignee_id=None):
    """Broadcast task updates to relevant users"""
    if socketio:
        if project_id:
            socketio.emit('task_updated', task_data, room=f"project_{project_id}")
        if assignee_id:
            socketio.emit('task_updated', task_data, room=f"user_{assignee_id}")
        logger.info(f"Task update broadcast: Task ID {task_data.get('id', 'Unknown ID')}")


def emit_test_notification(user_id, message="Test notification"):
    """Send a test notification to a specific user (for testing)"""
    test_data = {
        'id': 'test',
        'type': 'info',
        'title': 'Test Notification',
        'message': message,
        'created_at': str(datetime.utcnow())
    }
    broadcast_notification(user_id, test_data)
    logger.info(f"Test notification sent to user {user_id}")

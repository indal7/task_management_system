"""
Simple, organized logging configuration for Task Management System
"""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """Add colors to console logging"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logging(app):
    """Setup comprehensive logging for the application"""
    
    # Create logs directory
    log_dir = Path(app.instance_path).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Get log level from config
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    
    # Configure root logger
    logging.basicConfig(level=log_level, handlers=[])
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 1. Console Handler (colored, simple format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(colored_formatter)
    
    # 2. Application Log File (detailed format)
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(detailed_formatter)
    
    # 3. Error Log File (errors only)
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'errors.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Configure Flask app logger
    app.logger.handlers.clear()
    app.logger.addHandler(console_handler)
    app.logger.addHandler(app_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(log_level)
    
    # Configure other loggers
    loggers_to_configure = [
        'werkzeug',       # Flask dev server
        'sqlalchemy',     # Database queries
        'socketio',       # Socket.IO
        'celery',         # Background tasks
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.addHandler(app_handler)
        logger.setLevel(logging.WARNING)  # Less verbose for third-party
        logger.propagate = True
    
    # Custom application loggers
    setup_custom_loggers(app_handler, error_handler, log_level)
    
    app.logger.info("🔧 Logging system initialized")
    app.logger.info(f"📁 Log directory: {log_dir}")
    app.logger.info(f"📊 Log level: {logging.getLevelName(log_level)}")

def setup_custom_loggers(app_handler, error_handler, log_level):
    """Setup custom loggers for different parts of the application"""
    
    custom_loggers = {
        'auth': 'Authentication & Authorization',
        'tasks': 'Task Management',
        'projects': 'Project Management', 
        'cache': 'Caching System',
        'socket': 'Real-time Communications',
        'api': 'API Requests',
        'db': 'Database Operations'
    }
    
    for name, description in custom_loggers.items():
        logger = logging.getLogger(f'app.{name}')
        logger.handlers.clear()
        logger.addHandler(app_handler)
        logger.addHandler(error_handler)
        logger.setLevel(log_level)
        logger.propagate = True

def get_logger(name):
    """Get a logger for a specific module"""
    return logging.getLogger(f'app.{name}')

# Convenience functions for different log types
def log_api_request(endpoint, method, user_id=None, ip=None):
    """Log API requests"""
    logger = get_logger('api')
    logger.info(f"📡 {method} {endpoint} | User: {user_id} | IP: {ip}")

def log_db_query(query_type, table, duration_ms=None):
    """Log database operations"""
    logger = get_logger('db')
    duration = f" | {duration_ms}ms" if duration_ms else ""
    logger.debug(f"🗄️ {query_type} on {table}{duration}")

def log_cache_operation(operation, key, hit=None):
    """Log cache operations"""
    logger = get_logger('cache')
    status = "HIT" if hit else "MISS" if hit is False else ""
    logger.debug(f"⚡ Cache {operation}: {key} {status}")

def log_socket_event(event, user_id=None, room=None):
    """Log socket events"""
    logger = get_logger('socket')
    logger.info(f"🔌 Socket {event} | User: {user_id} | Room: {room}")

def log_auth_event(event, user_id=None, email=None, success=True):
    """Log authentication events"""
    logger = get_logger('auth')
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"🔐 {event} {status} | User: {user_id} | Email: {email}")



from functools import wraps
from flask import request, current_app as app
from .logger import get_logger

def log_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger('api')
        endpoint = request.path
        method = request.method
        user_ip = request.remote_addr
        data = request.get_json(silent=True)
        email = data.get('email') if data else None

        logger.info(f"API called | Endpoint: {endpoint} | Method: {method} | Email: {email} | IP: {user_ip}")

        return func(*args, **kwargs)
    return wrapper

"""
Configuration module for Task Management System
"""

from .base import BaseConfig
from .dev import DevelopmentConfig

# Configuration mapping
configs = {
    'development': DevelopmentConfig,
    'dev': DevelopmentConfig,
}

def get_config(config_name='development'):
    """Get configuration class by name"""
    return configs.get(config_name.lower(), DevelopmentConfig)

__all__ = [
    'BaseConfig',
    'DevelopmentConfig',
    'get_config',
]

"""
Configuration module for Task Management System
"""

from .base import BaseConfig
from .dev import DevelopmentConfig
from .testing import TestingConfig
from .production import ProductionConfig

# Configuration mapping
configs = {
    'development': DevelopmentConfig,
    'dev': DevelopmentConfig,
    'testing': TestingConfig,
    'test': TestingConfig,
    'production': ProductionConfig,
    'prod': ProductionConfig,
}

def get_config(config_name='development'):
    """Get configuration class by name"""
    return configs.get(config_name.lower(), DevelopmentConfig)

__all__ = [
    'BaseConfig',
    'DevelopmentConfig',
    'TestingConfig',
    'ProductionConfig',
    'get_config',
]

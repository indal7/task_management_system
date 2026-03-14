"""
Configuration module for Task Management System
"""

from .base import BaseConfig
from .dev import DevelopmentConfig
# from .staging import StagingConfig
# from .production import ProductionConfig
# from .testing import TestingConfig

# Configuration mapping
configs = {
    'development': DevelopmentConfig,
    'dev': DevelopmentConfig,
    # 'staging': StagingConfig,
    # 'production': ProductionConfig,
    # 'prod': ProductionConfig,
    # 'testing': TestingConfig,
    # 'test': TestingConfig,
}

def get_config(config_name='development'):
    """Get configuration class by name"""
    return configs.get(config_name.lower(), DevelopmentConfig)

__all__ = [
    'BaseConfig',
    'DevelopmentConfig', 
    # 'StagingConfig',
    # 'ProductionConfig',
    # 'TestingConfig',
    # 'get_config'
]
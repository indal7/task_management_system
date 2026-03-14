from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Development environment settings."""
    
    # Fix these settings:
    DEBUG = True                    # Enable debug mode
    SQLALCHEMY_ECHO = True         # Enable SQL query logging
    FLASK_ENV = 'development'
    
    # Your database URL is fine
    SQLALCHEMY_DATABASE_URI = 'postgresql://myuser:MySecurePassword123%21@dev-database.c1qe2o6s6oix.ap-south-1.rds.amazonaws.com:5432/myapp?sslmode=require'
    # DATABASE_URL=postgresql://myuser:MySecurePassword123%21@dev-database.c1qe2o6s6oix.ap-south-1.rds.amazonaws.com:5432/myapp?sslmode=require
    
    # Add these for API development
    WTF_CSRF_ENABLED = False       # Disable CSRF for API testing
    TESTING = False
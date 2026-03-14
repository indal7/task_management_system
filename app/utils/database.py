# app/utils/database.py
from sqlalchemy import text
from app import db

def init_database():
    """Create all tables (development use only)"""
    db.create_all()

def test_connection():
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
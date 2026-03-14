# app/utils/database.py
from app import db

def init_database():
    """Create all tables (development use only)"""
    db.create_all()

def test_connection():
    try:
        # Change this line:
        db.session.execute("SELECT 1")
        # To this:
        from sqlalchemy import text
        db.session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

#!/usr/bin/env python3
"""
Ultra Simple Management commands for Task Management System
"""

import os
import sys
import click
from pathlib import Path
from sqlalchemy import inspect

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))


def get_minimal_app(env='development'):
    """Minimal Flask app for DB operations only (no blueprints, no socketio, no logging)"""
    from dotenv import load_dotenv
    from flask import Flask
    from app import db
    import app.models  # ensures all models are imported
    from config import get_config

    # Load environment variables
    env_file = f"env/.env.{env}"
    if os.path.exists(env_file):
        load_dotenv(env_file)

    # Minimal Flask app
    app = Flask(__name__)
    app.config.from_object(get_config(env))
    db.init_app(app)

    return app



@click.group()
def cli():
    """Task Management System CLI"""
    pass


@cli.command()
@click.option('--env', default='development', help='Environment to use')
def create_db(env):
    """Create all tables"""
    print(f"🔧 Creating tables for {env} environment...")
    app = get_minimal_app(env)
    print(f"type(app) = {type(app)}")  # Should be <class 'flask.app.Flask'>

    with app.app_context():
        from app import db
        try:
            db.create_all()
            print("✅ All tables created successfully!")

            # Show tables
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Tables: {', '.join(tables) if tables else 'None found'}")

        except Exception as e:
            print(f"❌ Failed: {e}")


@cli.command()
@click.option('--env', default='development', help='Environment to use')
def drop_db(env):
    """Drop all tables"""
    if click.confirm(f'⚠️  Drop ALL tables in {env}?'):
        app = get_minimal_app(env)
        with app.app_context():
            from app import db
            try:
                db.drop_all()
                print("✅ All tables dropped!")
            except Exception as e:
                print(f"❌ Failed to drop tables: {e}")


@cli.command()
@click.option('--env', default='development', help='Environment to use')
def reset_db(env):
    """Drop and recreate all tables"""
    print(f"🔄 Resetting database...")
    app = get_minimal_app(env)
    with app.app_context():
        from app import db
        try:
            db.drop_all()
            print("🗑️ Dropped tables")
            db.create_all()
            print("✅ Recreated tables")

            # Show result
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Tables: {', '.join(tables) if tables else 'None found'}")
        except Exception as e:
            print(f"❌ Reset failed: {e}")


@cli.command()
@click.option('--env', default='development', help='Environment to use')
def show_tables(env):
    """Show all tables"""
    app = get_minimal_app(env)
    with app.app_context():
        from app import db
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            print(f"📊 Tables in {env}:")
            if tables:
                for i, table in enumerate(tables, 1):
                    print(f"  {i}. {table}")
            else:
                print("  No tables found")
        except Exception as e:
            print(f"❌ Failed: {e}")


@cli.command()
@click.option('--env', default='development', help='Environment to use')
def run(env):
    """Run the development server"""
    os.environ['FLASK_ENV'] = env
    from app import create_app
    from config import get_config

    app = create_app(get_config(env))
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', True))


if __name__ == '__main__':
    cli()

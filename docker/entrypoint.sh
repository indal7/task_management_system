#!/bin/sh
# Entrypoint for production container.
# Runs Flask-Migrate upgrade to apply any pending migrations,
# then hands off to the main CMD (gunicorn).
set -e

echo "⏳ Running database migrations..."
flask db upgrade
echo "✅ Migrations applied"

exec "$@"

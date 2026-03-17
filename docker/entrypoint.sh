#!/bin/sh
# Entrypoint for production container.
# Runs Flask-Migrate upgrade only when explicitly enabled,
# then hands off to the main CMD (gunicorn).
set -e

if [ "${RUN_DB_MIGRATIONS_ON_START:-0}" = "1" ]; then
	echo "⏳ Running database migrations (startup mode enabled)..."
	flask db upgrade
	echo "✅ Migrations applied"
else
	echo "ℹ️ Skipping startup migrations (RUN_DB_MIGRATIONS_ON_START=${RUN_DB_MIGRATIONS_ON_START:-0})"
fi

exec "$@"

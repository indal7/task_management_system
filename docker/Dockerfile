# Production Dockerfile – uses production requirements and Gunicorn
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi:app \
    FLASK_ENV=production

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy production requirements first for layer caching
COPY requirements/base.txt requirements/base.txt
COPY requirements/production.txt requirements/production.txt

# Install base + production Python dependencies
RUN pip install --no-cache-dir -r requirements/base.txt -r requirements/production.txt

# Copy the application code
COPY . .

# Copy and configure entrypoint (runs DB migrations then starts app)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 5000

# Liveness probe – used by Docker and orchestrators
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run migrations then start Gunicorn
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gevent", "wsgi:app"]
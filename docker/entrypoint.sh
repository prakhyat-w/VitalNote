#!/bin/sh
set -e

if [ "$APP_ROLE" = "worker" ]; then
    echo "Starting Celery worker..."
    exec celery -A config worker --loglevel=info --concurrency=2
else
    echo "Running migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    echo "Starting Gunicorn..."
    exec gunicorn config.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers 2 \
        --timeout 120 \
        --worker-tmp-dir /dev/shm \
        --log-level info
fi

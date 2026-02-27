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
    # Change cwd to /dev/shm so gunicorn's control socket (.ctl) lands on
    # tmpfs — VirtioFS (/app) does not support Unix domain sockets on
    # Docker Desktop for Mac / ARM64 Linux.
    # PYTHONPATH keeps the app importable from the new cwd.
    export PYTHONPATH=/app
    if [ "$DEBUG" = "True" ]; then
        # Development: single worker with auto-reload on file changes
        cd /dev/shm && exec gunicorn config.wsgi:application \
            --bind 0.0.0.0:${PORT:-8000} \
            --workers 1 \
            --reload \
            --reload-extra-file /app/templates \
            --timeout 120 \
            --worker-tmp-dir /dev/shm \
            --log-level info
    else
        # Production: multiple workers, no reload
        cd /dev/shm && exec gunicorn config.wsgi:application \
            --bind 0.0.0.0:${PORT:-8000} \
            --workers 2 \
            --timeout 120 \
            --worker-tmp-dir /dev/shm \
            --log-level info
    fi
fi

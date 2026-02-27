#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting supervisord (gunicorn + celery)..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/vitalnote.conf

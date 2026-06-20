#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
echo "Starting gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn pazhooheshsaraa.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -

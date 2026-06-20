#!/bin/sh
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Ensuring cache table exists..."
python manage.py createcachetable 2>/dev/null || true

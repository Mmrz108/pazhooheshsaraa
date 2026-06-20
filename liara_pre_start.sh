#!/bin/sh

echo "=== liara_pre_start.sh ==="
mkdir -p media cache staticfiles

echo "Running database migrations..."
if ! python manage.py migrate --noinput; then
  echo "ERROR: database migration failed."
  exit 1
fi

echo "Ensuring cache table exists..."
python manage.py createcachetable 2>/dev/null || true

echo "Pre-start finished."

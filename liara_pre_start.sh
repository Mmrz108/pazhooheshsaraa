#!/bin/sh

echo "=== liara_pre_start.sh ==="
mkdir -p media cache staticfiles

echo "Checking database configuration..."
python - <<'PY'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pazhooheshsaraa.settings')
django.setup()
from django.conf import settings
engine = settings.DATABASES['default']['ENGINE']
host = settings.DATABASES['default'].get('HOST', '')
print(f"DB engine: {engine}")
print(f"DB host: {host}")
if 'sqlite' in engine:
    raise SystemExit('ERROR: SQLite is not supported on Liara. Set USE_SQLITE=False and configure PostgreSQL.')
if 'postgresql' in engine and host in ('', 'localhost', '127.0.0.1'):
    raise SystemExit('ERROR: PostgreSQL env vars are missing. Set POSTGRESQL_DB_* in Liara console.')
PY

echo "Running database migrations..."
if ! python manage.py migrate --noinput; then
  echo "ERROR: database migration failed."
  exit 1
fi

echo "Ensuring cache table exists..."
python manage.py createcachetable 2>/dev/null || true

echo "Pre-start finished."

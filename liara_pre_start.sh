#!/bin/sh
set -e

echo "=== liara_pre_start.sh ==="
mkdir -p media cache staticfiles

echo "Checking database configuration..."
python <<'PY'
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pazhooheshsaraa.settings')

import django
django.setup()

from django.conf import settings

engine = settings.DATABASES['default']['ENGINE']
host = settings.DATABASES['default'].get('HOST', '')
name = settings.DATABASES['default'].get('NAME', '')
user = settings.DATABASES['default'].get('USER', '')
port = settings.DATABASES['default'].get('PORT', '')

print(f'DB engine: {engine}')
print(f'DB host: {host or "(empty)"}')
print(f'DB name: {name or "(empty)"}')
print(f'DB user: {user or "(empty)"}')
print(f'DB port: {port or "(empty)"}')

URL_KEYS = ('DATABASE_URL', 'POSTGRESQL_URI', 'POSTGRES_URI')
PG_KEYS = {
    'POSTGRESQL_DB_HOST': ('POSTGRESQL_DB_HOST', 'DB_HOST'),
    'POSTGRESQL_DB_PORT': ('POSTGRESQL_DB_PORT', 'DB_PORT'),
    'POSTGRESQL_DB_USER': ('POSTGRESQL_DB_USER', 'DB_USER'),
    'POSTGRESQL_DB_PASS': ('POSTGRESQL_DB_PASS', 'DB_PASSWORD'),
    'POSTGRESQL_DB_NAME': ('POSTGRESQL_DB_NAME', 'DB_NAME'),
}

database_url = next((os.getenv(k) for k in URL_KEYS if os.getenv(k)), '')
missing = []

print('--- env vars ---')
print(f'USE_SQLITE: {os.getenv("USE_SQLITE", "(not set)")}')
if database_url:
    print('DATABASE_URL: set')
else:
    print('DATABASE_URL: MISSING')
    for label, keys in PG_KEYS.items():
        value = next((os.getenv(k) for k in keys if os.getenv(k)), '')
        if value:
            if 'PASS' in label:
                print(f'{label}: set')
            else:
                print(f'{label}: {value}')
        else:
            print(f'{label}: MISSING')
            missing.append(label)

if 'sqlite' in engine:
    print('FATAL: SQLite is not supported on Liara. Set USE_SQLITE=False.')
    sys.exit(1)

if os.getenv('USE_SQLITE', '').lower() in ('1', 'true', 'yes'):
    print('FATAL: USE_SQLITE must be False on Liara.')
    sys.exit(1)

if 'postgresql' in engine and host in ('', 'localhost', '127.0.0.1'):
    print('')
    print('FATAL: PostgreSQL is not configured.')
    print('In Liara Console:')
    print('  1) Databases -> PostgreSQL -> open your database')
    print('  2) Copy connection info from the Connection tab')
    print('  3) App test-mirzaei -> Settings -> Environment Variables')
    print('  4) Either set DATABASE_URL=postgresql://USER:PASS@HOST:PORT/DBNAME')
    print('     OR set POSTGRESQL_DB_HOST/PORT/USER/PASS/NAME from the panel')
    print('  5) Set USE_SQLITE=False and redeploy')
    if not database_url and missing:
        print('')
        print('Missing vars:', ', '.join(missing))
    sys.exit(1)
PY

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Ensuring cache table exists..."
python manage.py createcachetable 2>/dev/null || true

echo "Pre-start finished."

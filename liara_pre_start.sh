#!/bin/sh
set -e

echo "=== liara_pre_start.sh ==="

echo "Checking database configuration..."
python <<'PY'
import os
import sys
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pazhooheshsaraa.settings')

import django
django.setup()

from django.conf import settings

engine = settings.DATABASES['default']['ENGINE']
db_name = settings.DATABASES['default'].get('NAME', '')

print(f'DB engine: {engine}')
print(f'DB path/name: {db_name or "(empty)"}')
print(f'USE_SQLITE: {os.getenv("USE_SQLITE", "(not set, default=True)")}')
print(f'MEDIA_ROOT: {settings.MEDIA_ROOT}')

if 'sqlite' in engine:
    db_path = Path(str(db_name))
    write_dir = db_path.parent if db_path.suffix else db_path
    test_file = write_dir / '.write_test'
    try:
        test_file.write_text('ok', encoding='utf-8')
        test_file.unlink(missing_ok=True)
    except OSError as exc:
        print('')
        print('FATAL: SQLite/data directory is not writable.')
        print(f'Path: {write_dir}')
        print('In Liara Console create a disk named "data" and mount it to data/.')
        print(f'Error: {exc}')
        sys.exit(1)
    print('SQLite: writable OK')

    media_root = settings.MEDIA_ROOT
    media_test = Path(str(media_root)) / '.write_test'
    try:
        Path(str(media_root)).mkdir(parents=True, exist_ok=True)
        media_test.write_text('ok', encoding='utf-8')
        media_test.unlink(missing_ok=True)
    except OSError as exc:
        print('')
        print('FATAL: MEDIA_ROOT is not writable.')
        print(f'Path: {media_root}')
        print('In Liara Console create a disk named "media" and mount it to media/.')
        print(f'Error: {exc}')
        sys.exit(1)
    print(f'MEDIA_ROOT: writable OK ({media_root})')
    raise SystemExit(0)

host = settings.DATABASES['default'].get('HOST', '')
user = settings.DATABASES['default'].get('USER', '')
port = settings.DATABASES['default'].get('PORT', '')

print(f'DB host: {host or "(empty)"}')
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

if 'postgresql' in engine and host in ('', 'localhost', '127.0.0.1'):
    print('')
    print('FATAL: PostgreSQL is not configured.')
    print('Set USE_SQLITE=True for SQLite, or add POSTGRESQL_DB_* env vars.')
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

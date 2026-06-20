import os
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    OTP_EXPIRY_SECONDS=(int, 120),
    OTP_MAX_ATTEMPTS=(int, 5),
    OTP_RESEND_COOLDOWN_SECONDS=(int, 60),
    OTP_MAX_SENDS_PER_HOUR=(int, 5),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 60),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
    ZARINPAL_SANDBOX=(bool, True),
)

environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

_liara_app = os.getenv('LIARA_APP_NAME', '')
if _liara_app and f'{_liara_app}.liara.run' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(f'{_liara_app}.liara.run')
if '.liara.run' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.liara.run')

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
if _liara_app:
    _liara_origin = f'https://{_liara_app}.liara.run'
    if _liara_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_liara_origin)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    # Local apps
    'apps.users',
    'apps.courses',
    'apps.payments',
    'apps.content',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'common.middleware.AdminAccessMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pazhooheshsaraa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pazhooheshsaraa.wsgi.application'
ASGI_APPLICATION = 'pazhooheshsaraa.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRESQL_DB_NAME', default=env('DB_NAME', default='pazhooheshsaraa')),
        'USER': env('POSTGRESQL_DB_USER', default=env('DB_USER', default='postgres')),
        'PASSWORD': env('POSTGRESQL_DB_PASS', default=env('DB_PASSWORD', default='postgres')),
        'HOST': env('POSTGRESQL_DB_HOST', default=env('DB_HOST', default='localhost')),
        'PORT': env('POSTGRESQL_DB_PORT', default=env('DB_PORT', default='5432')),
    }
}

if env.bool('USE_SQLITE', default=False):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = env('STATIC_URL', default='/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / 'media'
FRONTEND_DIR = BASE_DIR / 'frontend'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redis
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')
USE_REDIS = env.bool('USE_REDIS', default=False)

if USE_REDIS:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': BASE_DIR / 'cache',
        }
    }

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'otp': '1000/hour' if DEBUG else '10/hour',
    },
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env('JWT_ACCESS_TOKEN_LIFETIME_MINUTES')),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env('JWT_REFRESH_TOKEN_LIFETIME_DAYS')),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# OTP Settings
OTP_EXPIRY_SECONDS = env('OTP_EXPIRY_SECONDS')
OTP_MAX_ATTEMPTS = env('OTP_MAX_ATTEMPTS')
OTP_RESEND_COOLDOWN_SECONDS = env('OTP_RESEND_COOLDOWN_SECONDS')
OTP_MAX_SENDS_PER_HOUR = env('OTP_MAX_SENDS_PER_HOUR')
OTP_DEBUG_VISIBLE = env.bool('OTP_DEBUG_VISIBLE', default=DEBUG)

# Admin site gate â€” staff must enter this password on /site-management/
ADMIN_SITE_PASSWORD = env(
    'ADMIN_SITE_PASSWORD',
    default='123456789' if DEBUG else '',
)
ADMIN_ACCESS_LOGIN_URL = '/site-management/'

# SMS
SMS_PROVIDER = env('SMS_PROVIDER', default='console')
SMS_API_KEY = env('SMS_API_KEY', default='')
SMS_SENDER = env('SMS_SENDER', default='')
KAVENEGAR_OTP_TEMPLATE = env('KAVENEGAR_OTP_TEMPLATE', default='otp')
SMS_FALLBACK_CONSOLE = env.bool('SMS_FALLBACK_CONSOLE', default=False)

# Bale Safir OTP (https://docs.bale.ai/safir)
BALE_ENABLED = env.bool('BALE_ENABLED', default=False)
BALE_BOT_ID = int(env('BALE_BOT_ID', default='0') or 0)
BALE_BOT_TOKEN = env('BALE_BOT_TOKEN', default='')
BALE_BOT_USERNAME = env('BALE_BOT_USERNAME', default='')
BALE_API_ACCESS_KEY = env('BALE_API_ACCESS_KEY', default='')
BALE_CLIENT_ID = env('BALE_CLIENT_ID', default='')
BALE_CLIENT_SECRET = env('BALE_CLIENT_SECRET', default='')
BALE_API_URL = env(
    'BALE_API_URL',
    default='https://safir.bale.ai/api/v3/send_message',
)
BALE_GATEWAY_TOKEN_URL = env(
    'BALE_GATEWAY_TOKEN_URL',
    default='https://safir.bale.ai/api/v2/auth/token',
)
BALE_GATEWAY_OTP_URL = env(
    'BALE_GATEWAY_OTP_URL',
    default='https://safir.bale.ai/api/v2/send_otp',
)

# Payment
ZARINPAL_MERCHANT_ID = env('ZARINPAL_MERCHANT_ID', default='')
ZARINPAL_SANDBOX = env('ZARINPAL_SANDBOX')
PAYMENT_CALLBACK_URL = env(
    'PAYMENT_CALLBACK_URL',
    default='http://localhost:8000/api/payments/verify/',
)

# Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


try:
    from .celery import app as celery_app
except Exception:  # pragma: no cover - optional on Liara without Celery worker
    celery_app = None

__all__ = ('celery_app',)

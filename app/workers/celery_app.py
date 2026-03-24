from celery import Celery

celery_app = Celery(
    "taskmanager",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

# Try to load settings from env, with fallbacks
try:
    from app.core.config import settings
    celery_app.conf.broker_url = settings.CELERY_BROKER_URL
    celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND
except Exception:
    pass

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.autodiscover_tasks(["app.workers"])

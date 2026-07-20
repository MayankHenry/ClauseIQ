"""
Celery app instance. Start a worker with:
    celery -A app.workers.celery_app worker --loglevel=info
(on Windows, add --pool=solo — Celery's default worker pool doesn't
support Windows well)
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "clauseiq",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.ingestion"],
)

"""Celery task queue configuration for async task processing.

This module initializes the Celery application with Redis as the broker
and backend, configured for JSON serialization and task tracking.
"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "criterion",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.analysis"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,  # Only ack after task completes — prevents lost tasks
)

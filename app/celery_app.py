import os

from celery import Celery
from celery.signals import worker_ready, worker_shutdown

from .health_bus import emit_service_health


celery = Celery(
    "real_time_data_engineering",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
)

celery.conf.task_default_queue = "default"
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.accept_content = ["json"]
celery.conf.task_acks_late = True

celery.autodiscover_tasks(["app"])


@worker_ready.connect
def handle_worker_ready(sender=None, **kwargs):
    emit_service_health(
        os.getenv("WORKER_LABEL", "celery-worker"),
        "healthy",
        "Celery worker ready",
    )


@worker_shutdown.connect
def handle_worker_shutdown(sender=None, **kwargs):
    emit_service_health(
        os.getenv("WORKER_LABEL", "celery-worker"),
        "degraded",
        "Celery worker shutting down",
    )


if __name__ == "__main__":
    celery.start()

import os

import socketio

from .celery_app import celery


socketio_message_queue = socketio.RedisManager(
    os.getenv("SOCKETIO_REDIS_URL", "redis://redis:6379/2"),
    write_only=True,
)


def emit_task_update(event_name, payload):
    socketio_message_queue.emit(event_name, payload)


@celery.task(name="app.tasks.process_message")
def process_message(payload):
    result = {
        "status": "processed",
        "payload": payload,
    }

    emit_task_update("task_completed", result)
    return result

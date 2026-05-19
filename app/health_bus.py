import json
import os
import time

import redis
import socketio


REDIS_URL = os.getenv("SOCKETIO_REDIS_URL", "redis://redis:6379/2")

socketio_message_queue = socketio.RedisManager(REDIS_URL, write_only=True)
redis_client = redis.Redis.from_url(REDIS_URL)


def emit_service_health(service, status, message, extra=None):
    payload = {
        "service": service,
        "status": status,
        "message": message,
        "timestamp": int(time.time() * 1000),
    }

    if extra:
        payload.update(extra)

    try:
        socketio_message_queue.emit("service_health", payload)
    except Exception:
        pass

    try:
        redis_client.set(f"health:{service}", json.dumps(payload), ex=45)
    except Exception:
        pass

    return payload
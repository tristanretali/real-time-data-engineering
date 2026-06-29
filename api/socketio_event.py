import json
import os

import redis
import socketio

REDIS_URL = os.getenv("SOCKETIO_REDIS_URL", "redis://redis:6379/2")
SNAPSHOT_TTL_SECONDS = int(os.getenv("RECENT_TRADES_SNAPSHOT_TTL", "120"))

socketio_manager = socketio.RedisManager(
    REDIS_URL,
    write_only=True,
)

redis_client = redis.Redis.from_url(REDIS_URL)


def save_snapshot(name: str, payload: dict) -> dict:
    redis_client.setex(f"snapshot:{name}", SNAPSHOT_TTL_SECONDS, json.dumps(payload))
    return payload


def get_snapshot(name: str) -> dict | None:
    raw = redis_client.get(f"snapshot:{name}")
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def emit_event(name: str, payload: dict) -> dict:
    socketio_manager.emit(name, payload)
    return payload


def publish(name: str, payload: dict) -> dict:
    save_snapshot(name, payload)
    emit_event(name, payload)
    return payload


def get_recent_trades_snapshot():
    return get_snapshot("recent_trades")


def get_volume_snapshot():
    return get_snapshot("volume")


def get_price_snapshot():
    return get_snapshot("price")


def get_alerts_snapshot():
    return get_snapshot("alerts")

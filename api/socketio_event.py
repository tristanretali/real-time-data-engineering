import os
import json
import socketio
import redis

REDIS_URL = os.getenv("SOCKETIO_REDIS_URL", "redis://redis:6379/2")
SNAPSHOT_TTL_SECONDS = int(os.getenv("RECENT_TRADES_SNAPSHOT_TTL", "120"))

socketio_manager = socketio.RedisManager(
    REDIS_URL,
    write_only=True,
)

redis_client = redis.Redis.from_url(REDIS_URL)


def save_recent_trades_snapshot(trades: list):
    payload = {
        "recent_trades": trades,
    }
    redis_client.setex(
        "snapshot:recent_trades", SNAPSHOT_TTL_SECONDS, json.dumps(payload)
    )
    return payload


def save_volume_snapshot(volume: dict):
    redis_client.setex("snapshot:volume", SNAPSHOT_TTL_SECONDS, json.dumps(volume))
    return volume


def save_price_snapshot(price: dict):
    redis_client.setex("snapshot:price", SNAPSHOT_TTL_SECONDS, json.dumps(price))
    return price


def get_recent_trades_snapshot():
    raw = redis_client.get("snapshot:recent_trades")
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def get_volume_snapshot():
    raw = redis_client.get("snapshot:volume")
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def get_price_snapshot():
    raw = redis_client.get("snapshot:price")
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def emit_recent_trades(trades: list):
    payload = {
        "recent_trades": trades,
    }
    socketio_manager.emit("recent_trades", payload)
    return payload


def emit_volume(volume: dict):
    socketio_manager.emit("volume", volume)
    return volume


def emit_price(price: dict):
    socketio_manager.emit("price", price)
    return price

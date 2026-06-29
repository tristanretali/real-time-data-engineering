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


def save_alerts_snapshot(alerts: dict):
    redis_client.setex("snapshot:alerts", SNAPSHOT_TTL_SECONDS, json.dumps(alerts))
    return alerts


def save_trade_rate_snapshot(trade_rate: dict):
    redis_client.setex(
        "snapshot:trade_rate", SNAPSHOT_TTL_SECONDS, json.dumps(trade_rate)
    )
    return trade_rate


def save_price_history_snapshot(price_history: dict):
    redis_client.setex(
        "snapshot:price_history", SNAPSHOT_TTL_SECONDS, json.dumps(price_history)
    )
    return price_history


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


def get_alerts_snapshot():
    raw = redis_client.get("snapshot:alerts")
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


def emit_alerts(alerts: dict):
    socketio_manager.emit("alerts", alerts)
    return alerts


def emit_trade_rate(trade_rate: dict):
    socketio_manager.emit("trade_rate", trade_rate)
    return trade_rate


def emit_price_history(price_history: dict):
    socketio_manager.emit("price_history", price_history)
    return price_history

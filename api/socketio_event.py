import os
import socketio

socketio_manager = socketio.RedisManager(
    os.getenv("SOCKETIO_REDIS_URL", "redis://redis:6379/2"),
    write_only=True,
)


def emit_recent_trades(trades: list):
    payload = {
        "recent_trades": trades,
    }
    socketio_manager.emit("recent_trades", payload)
    return payload

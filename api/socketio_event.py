import os
import socketio

socketio_manager = socketio.RedisManager(
    os.getenv("SOCKETIO_REDIS_URL", "redis://redis:6379/2"),
    write_only=True,
)


def emit_test_event():
    payload = {
        "kind": "test",
        "message": "route /test triggered",
        "symbol": "BTCUSDT",
    }
    socketio_manager.emit("test", payload)
    return payload

import os

import socketio

from .health_bus import emit_service_health
from api.socketio_event import get_recent_trades_snapshot

socketio_message_queue = socketio.AsyncRedisManager(
    os.getenv("SOCKETIO_REDIS_URL", "redis://redis:6379/2")
)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    client_manager=socketio_message_queue,
)
app = socketio.ASGIApp(sio)


@sio.event
async def connect(sid, environ):
    try:
        emit_service_health("socketio", "healthy", "Socket.IO backend connected")
    except Exception:
        pass
    await sio.emit("server_ready", {"message": "Socket.IO connected"}, to=sid)

    snapshot = get_recent_trades_snapshot()
    if snapshot:
        await sio.emit("recent_trades", snapshot, to=sid)


@sio.event
async def disconnect(sid):
    return None


@sio.event
async def ping(sid, data):
    await sio.emit("pong", data, to=sid)

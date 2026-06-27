import os

import socketio

from .health_bus import emit_service_health
from api.socketio_event import (
    get_recent_trades_snapshot,
    get_volume_snapshot,
    get_price_snapshot,
    get_alerts_snapshot,
)

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

    recent_trades_snapshot = get_recent_trades_snapshot()
    if recent_trades_snapshot:
        await sio.emit("recent_trades", recent_trades_snapshot, to=sid)

    volume_snapshot = get_volume_snapshot()
    if volume_snapshot:
        await sio.emit("volume", volume_snapshot, to=sid)

    price_snapshot = get_price_snapshot()
    if price_snapshot:
        await sio.emit("price", price_snapshot, to=sid)

    alerts_snapshot = get_alerts_snapshot()
    if alerts_snapshot:
        await sio.emit("alerts", alerts_snapshot, to=sid)


@sio.event
async def disconnect(sid):
    return None


@sio.event
async def ping(sid, data):
    await sio.emit("pong", data, to=sid)

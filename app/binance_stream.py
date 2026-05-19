import asyncio
import collections
import json
import os
import time

import websockets

from .health_bus import emit_service_health

SYMBOL = os.getenv("BINANCE_SYMBOL", "btcusdt").lower()
WINDOW_SECONDS = int(os.getenv("VOLUME_WINDOW_SECONDS", "60"))
RECENT_TRADES_LIMIT = int(os.getenv("RECENT_TRADES_LIMIT", "20"))
MESSAGE_TIMEOUT_SECONDS = int(os.getenv("BINANCE_MESSAGE_TIMEOUT_SECONDS", "45"))
MAX_RECONNECT_DELAY_SECONDS = int(os.getenv("BINANCE_RECONNECT_MAX_DELAY_SECONDS", "30"))
BINANCE_WS_URL = os.getenv(
    "BINANCE_WS_URL",
    f"wss://stream.binance.com:9443/ws/{SYMBOL}@trade",
)


class BtcStreamState:
    def __init__(self):
        self.recent_trades = collections.deque(maxlen=RECENT_TRADES_LIMIT)
        self.last_heartbeat = 0

    def record_trade(self, trade):
        now_ms = int(time.time() * 1000)
        if now_ms - self.last_heartbeat >= 15000:
            emit_service_health(
                "binance-stream",
                "healthy",
                "BTC websocket active",
                {"symbol": trade["s"].upper()},
            )
            self.last_heartbeat = now_ms


async def stream_btc_trades():
    state = BtcStreamState()
    reconnect_delay = 1

    while True:
        try:
            emit_service_health(
                "binance-stream",
                "healthy",
                "Connecting to Binance BTC websocket",
                {"symbol": SYMBOL.upper()},
            )
            async with websockets.connect(
                BINANCE_WS_URL,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
            ) as websocket:
                emit_service_health(
                    "binance-stream",
                    "healthy",
                    "Connected to Binance BTC websocket",
                    {"symbol": SYMBOL.upper()},
                )
                reconnect_delay = 1
                while True:
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=MESSAGE_TIMEOUT_SECONDS,
                    )
                    trade = json.loads(message)
                    state.record_trade(trade)
        except (asyncio.TimeoutError, websockets.ConnectionClosed, OSError, json.JSONDecodeError) as exc:
            emit_service_health(
                "binance-stream",
                "degraded",
                f"Reconnecting in {reconnect_delay}s: {exc}",
                {"symbol": SYMBOL.upper()},
            )
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, MAX_RECONNECT_DELAY_SECONDS)
        except Exception as exc:
            emit_service_health(
                "binance-stream",
                "degraded",
                f"Unexpected error, reconnecting in {reconnect_delay}s: {exc}",
                {"symbol": SYMBOL.upper()},
            )
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, MAX_RECONNECT_DELAY_SECONDS)


def main():
    asyncio.run(stream_btc_trades())


if __name__ == "__main__":
    main()
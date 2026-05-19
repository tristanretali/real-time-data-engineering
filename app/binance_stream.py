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

    while True:
        try:
            async with websockets.connect(BINANCE_WS_URL, ping_interval=20, ping_timeout=20) as websocket:
                emit_service_health("binance-stream", "healthy", "Connected to Binance BTC websocket", {"symbol": SYMBOL.upper()})
                while True:
                    message = await websocket.recv()
                    trade = json.loads(message)
                    state.record_trade(trade)
        except Exception as exc:
            emit_service_health("binance-stream", "degraded", f"Reconnecting: {exc}", {"symbol": SYMBOL.upper()})
            await asyncio.sleep(5)


def main():
    asyncio.run(stream_btc_trades())


if __name__ == "__main__":
    main()
import asyncio
import collections
import json
import os
import time

import websockets
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable, NodeNotReadyError

from .health_bus import emit_service_health

SYMBOL = os.getenv("BINANCE_SYMBOL", "btcusdt").lower()
WINDOW_SECONDS = int(os.getenv("VOLUME_WINDOW_SECONDS", "60"))
RECENT_TRADES_LIMIT = int(os.getenv("RECENT_TRADES_LIMIT", "20"))
MESSAGE_TIMEOUT_SECONDS = int(os.getenv("BINANCE_MESSAGE_TIMEOUT_SECONDS", "45"))
MAX_RECONNECT_DELAY_SECONDS = int(os.getenv("BINANCE_RECONNECT_MAX_DELAY_SECONDS", "30"))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "binance.trades")
BINANCE_WS_URL = os.getenv(
    "BINANCE_WS_URL",
    f"wss://stream.binance.com:9443/ws/{SYMBOL}@trade",
)


class BtcStreamState:
    def __init__(self):
        self.recent_trades = collections.deque(maxlen=RECENT_TRADES_LIMIT)
        self.last_heartbeat = 0

    def record_trade(self, trade):
        self.recent_trades.append(trade)
        now_ms = int(time.time() * 1000)
        if now_ms - self.last_heartbeat >= 15000:
            emit_service_health(
                "binance-stream",
                "healthy",
                f"Published Binance trades to Kafka topic {KAFKA_TOPIC}",
                {"symbol": trade["s"].upper(), "recent_trades": len(self.recent_trades)},
            )
            self.last_heartbeat = now_ms


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
        retries=5,
        linger_ms=50,
    )


async def stream_btc_trades():
    state = BtcStreamState()
    reconnect_delay = 1
    producer = None

    while True:
        try:
            if producer is None:
                producer = create_producer()
            emit_service_health(
                "binance-stream",
                "healthy",
                "Connecting to Binance BTC websocket and Kafka",
                {"symbol": SYMBOL.upper(), "topic": KAFKA_TOPIC},
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
                    "Connected to Binance websocket",
                    {"symbol": SYMBOL.upper(), "topic": KAFKA_TOPIC},
                )
                reconnect_delay = 1
                while True:
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=MESSAGE_TIMEOUT_SECONDS,
                    )
                    trade = json.loads(message)
                    producer.send(KAFKA_TOPIC, trade).get(timeout=10)
                    state.record_trade(trade)
        except (
            asyncio.TimeoutError,
            websockets.ConnectionClosed,
            OSError,
            json.JSONDecodeError,
            KafkaError,
            NoBrokersAvailable,
            NodeNotReadyError,
        ) as exc:
            emit_service_health(
                "binance-stream",
                "degraded",
                f"Reconnecting in {reconnect_delay}s: {exc}",
                {"symbol": SYMBOL.upper(), "topic": KAFKA_TOPIC},
            )
            if producer is not None:
                producer.close()
                producer = None
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, MAX_RECONNECT_DELAY_SECONDS)
        except Exception as exc:
            emit_service_health(
                "binance-stream",
                "degraded",
                f"Unexpected error, reconnecting in {reconnect_delay}s: {exc}",
                {"symbol": SYMBOL.upper(), "topic": KAFKA_TOPIC},
            )
            if producer is not None:
                producer.close()
                producer = None
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, MAX_RECONNECT_DELAY_SECONDS)


def main():
    asyncio.run(stream_btc_trades())


if __name__ == "__main__":
    main()

import json
import os
import time

import socketio
from kafka import KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable, NodeNotReadyError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from api.constants import DEFAULT_SYMBOL
from api.routes import alerts, price, price_history, recent_trades, trade_rate, volume
from .health_bus import emit_service_health, redis_client


WORKER_LABEL = os.getenv("WORKER_LABEL", "kafka-worker")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "binance.trades")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "binance-trade-workers")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "market_data")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "binance_trades")

socketio_message_queue = socketio.RedisManager(
    os.getenv("SOCKETIO_REDIS_URL", "redis://redis:6379/2"),
    write_only=True,
)

METRIC_TRIGGERS = [
    ("recent_trades", recent_trades, 1, {"symbol": DEFAULT_SYMBOL, "limit": 5}),
    ("trade_rate", trade_rate, 1, {"symbol": DEFAULT_SYMBOL, "window_seconds": 60}),
    ("price", price, 5, {"symbol": DEFAULT_SYMBOL, "change_window_seconds": 900}),
    ("volume", volume, 5, {"symbol": DEFAULT_SYMBOL}),
    ("alerts", alerts, 5, {"symbol": DEFAULT_SYMBOL, "window_seconds": 300}),
    ("price_history", price_history, 60, {"symbol": DEFAULT_SYMBOL, "window_minutes": 15}),
]


def trigger_metric(label, fn, min_interval_seconds, kwargs):
    lock_acquired = redis_client.set(
        f"trigger:{label}", "1", nx=True, ex=min_interval_seconds
    )
    if not lock_acquired:
        return

    try:
        fn(**kwargs)
    except Exception as exc:
        print(f"trigger error [{label}]: {exc}")


def trigger_metrics_for_trade():
    for label, fn, min_interval_seconds, kwargs in METRIC_TRIGGERS:
        trigger_metric(label, fn, min_interval_seconds, kwargs)


def create_consumer():
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        consumer_timeout_ms=1000,
    )


def create_collection():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    collection = client[MONGODB_DATABASE][MONGODB_COLLECTION]
    collection.create_index("trade_id", unique=True)
    collection.create_index([("symbol", 1), ("trade_time", -1)])
    return client, collection


def normalize_trade(trade):
    return {
        "event_type": trade.get("e"),
        "trade_id": trade["t"],
        "symbol": trade["s"],
        "price": float(trade["p"]),
        "quantity": float(trade["q"]),
        "buyer_order_id": trade.get("b"),
        "seller_order_id": trade.get("a"),
        "trade_time": trade["T"],
        "event_time": trade["E"],
        "is_market_maker": trade.get("m"),
        "ignore_flag": trade.get("M"),
        "ingested_at": int(time.time() * 1000),
        "raw": trade,
    }


def emit_processed_event(document):
    socketio_message_queue.emit(
        "task_completed",
        {
            "status": "stored",
            "worker": WORKER_LABEL,
            "symbol": document["symbol"],
            "trade_id": document["trade_id"],
            "price": document["price"],
            "quantity": document["quantity"],
            "event_time": document["event_time"],
        },
    )


def run_worker():
    reconnect_delay = 1

    while True:
        consumer = None
        mongo_client = None
        try:
            emit_service_health(
                WORKER_LABEL,
                "healthy",
                "Connecting to Kafka and MongoDB",
                {"topic": KAFKA_TOPIC},
            )
            mongo_client, collection = create_collection()
            consumer = create_consumer()
            reconnect_delay = 1
            emit_service_health(
                WORKER_LABEL,
                "healthy",
                "Consuming Kafka trades into MongoDB",
                {"topic": KAFKA_TOPIC},
            )

            while True:
                for message in consumer:
                    trade = message.value
                    document = normalize_trade(trade)
                    try:
                        collection.update_one(
                            {"trade_id": document["trade_id"]},
                            {"$setOnInsert": document},
                            upsert=True,
                        )
                        consumer.commit()
                        emit_processed_event(document)
                        emit_service_health(
                            WORKER_LABEL,
                            "healthy",
                            f"Stored trade {document['trade_id']} in MongoDB",
                            {"symbol": document["symbol"]},
                        )
                        trigger_metrics_for_trade()
                    except PyMongoError as exc:
                        emit_service_health(
                            WORKER_LABEL,
                            "degraded",
                            f"MongoDB write failed: {exc}",
                        )
                        time.sleep(reconnect_delay)
                        break
        except (NoBrokersAvailable, NodeNotReadyError, KafkaError, PyMongoError, OSError, ValueError) as exc:
            emit_service_health(
                WORKER_LABEL,
                "degraded",
                f"Reconnect in {reconnect_delay}s: {exc}",
                {"topic": KAFKA_TOPIC},
            )
            time.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 30)
        finally:
            if consumer is not None:
                consumer.close()
            if mongo_client is not None:
                mongo_client.close()


def main():
    run_worker()


if __name__ == "__main__":
    main()

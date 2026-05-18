import json
import os
import socket
import time

from kafka import KafkaAdminClient

from .celery_app import celery
from .health_bus import emit_service_health, redis_client, socketio_message_queue


def check_tcp(host, port, timeout=3):
    with socket.create_connection((host, port), timeout=timeout):
        return True


def check_redis():
    return redis_client.ping()


def check_kafka():
    client = KafkaAdminClient(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        request_timeout_ms=3000,
        api_version_auto_timeout_ms=3000,
    )
    try:
        client.list_topics(timeout=3)
        return True
    finally:
        client.close()


def read_health_key(service, max_age_seconds=45):
    raw_value = redis_client.get(f"health:{service}")
    if not raw_value:
        return {
            "service": service,
            "status": "down",
            "message": "No heartbeat received",
            "timestamp": int(time.time() * 1000),
        }

    payload = json.loads(raw_value)
    age_seconds = (time.time() * 1000 - payload["timestamp"]) / 1000
    if age_seconds > max_age_seconds:
        payload["status"] = "degraded"
        payload["message"] = f"Heartbeat stale ({age_seconds:.0f}s)"
    payload["age_seconds"] = round(age_seconds, 1)
    return payload


def build_snapshot():
    services = []

    services.append(
        {
            "service": "redis",
            "status": "healthy" if check_redis() else "down",
            "message": "Redis broker reachable" if check_redis() else "Redis not reachable",
            "timestamp": int(time.time() * 1000),
        }
    )

    kafka_ok = False
    kafka_message = "Kafka not reachable"
    try:
        kafka_ok = check_kafka()
        kafka_message = "Kafka metadata reachable"
    except Exception as exc:
        kafka_message = str(exc)

    services.append(
        {
            "service": "kafka",
            "status": "healthy" if kafka_ok else "down",
            "message": kafka_message,
            "timestamp": int(time.time() * 1000),
        }
    )

    socketio_ok = False
    socketio_message = "Socket.IO not reachable"
    try:
        socketio_ok = check_tcp("socketio", 8000)
        socketio_message = "Socket.IO endpoint open"
    except Exception as exc:
        socketio_message = str(exc)

    services.append(
        {
            "service": "socketio",
            "status": "healthy" if socketio_ok else "down",
            "message": socketio_message,
            "timestamp": int(time.time() * 1000),
        }
    )

    for service_name in ["binance-stream", "celery-worker-1", "celery-worker-2", "celery-worker-3"]:
        services.append(read_health_key(service_name))

    healthy_count = sum(1 for service in services if service["status"] == "healthy")
    degraded_count = sum(1 for service in services if service["status"] == "degraded")
    down_count = sum(1 for service in services if service["status"] == "down")

    return {
        "kind": "orchestration_snapshot",
        "timestamp": int(time.time() * 1000),
        "summary": {
            "healthy": healthy_count,
            "degraded": degraded_count,
            "down": down_count,
            "total": len(services),
        },
        "services": services,
    }


def main():
    emit_service_health("orchestration-monitor", "healthy", "Orchestration monitor started")

    while True:
        try:
            snapshot = build_snapshot()
            socketio_message_queue.emit("orchestration_snapshot", snapshot)
            time.sleep(5)
        except Exception as exc:
            emit_service_health("orchestration-monitor", "degraded", f"Monitor error: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    main()
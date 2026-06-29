from datetime import datetime, timezone


def now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def ms_ago(reference_ms: int, seconds: float) -> int:
    return reference_ms - int(seconds * 1000)


def ms_to_iso(value_ms: int) -> str:
    return datetime.fromtimestamp(float(value_ms) / 1000.0, tz=timezone.utc).isoformat()

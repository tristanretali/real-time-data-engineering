import threading
import time
from typing import Callable

from fastapi import FastAPI

from .constants import DEFAULT_SYMBOL
from .routes import (
    alerts,
    price,
    price_history,
    recent_trades,
    router,
    trade_rate,
    volume,
)

app = FastAPI(title="API Dashboard Crypto")

FAST_DATA_PULL = 1
SLOW_DATA_PULL = 5
CHART_PULL = 60

FAST_JOBS = [
    ("recent_trades", recent_trades, {"symbol": DEFAULT_SYMBOL, "limit": 5}),
    ("trade_rate", trade_rate, {"symbol": DEFAULT_SYMBOL, "window_seconds": 60}),
]

SLOW_JOBS = [
    ("price", price, {"symbol": DEFAULT_SYMBOL, "change_window_seconds": 900}),
    ("volume", volume, {"symbol": DEFAULT_SYMBOL}),
    ("alerts", alerts, {"symbol": DEFAULT_SYMBOL, "window_seconds": 300}),
]

CHART_JOBS = [
    ("price_history", price_history, {"symbol": DEFAULT_SYMBOL, "window_minutes": 15}),
]


def safe_call(label: str, fn: Callable, **kwargs) -> None:
    try:
        fn(**kwargs)
    except Exception as exc:
        print(f"poll error [{label}]: {exc}")


def run_loop(interval_seconds: float, jobs: list[tuple[str, Callable, dict]]) -> None:
    while True:
        for label, fn, kwargs in jobs:
            safe_call(label, fn, **kwargs)
        time.sleep(interval_seconds)


@app.on_event("startup")
def start_market_data_pollers():
    threading.Thread(
        target=run_loop, args=(FAST_DATA_PULL, FAST_JOBS), daemon=True
    ).start()
    threading.Thread(
        target=run_loop, args=(SLOW_DATA_PULL, SLOW_JOBS), daemon=True
    ).start()
    threading.Thread(
        target=run_loop, args=(CHART_PULL, CHART_JOBS), daemon=True
    ).start()


app.include_router(router, prefix="/api")

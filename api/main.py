import threading
import time

from fastapi import FastAPI
from .routes import (
    router,
    alerts,
    price,
    price_history,
    recent_trades,
    trade_rate,
    volume,
)

app = FastAPI(title="API Dashboard Crypto")

FAST_POLL_SECONDS = 1
SLOW_POLL_SECONDS = 5
CHART_POLL_SECONDS = 20


def safe_call(label, fn, **kwargs):
    try:
        fn(**kwargs)
    except Exception as exc:
        print(f"poll error [{label}]: {exc}")


def poll_fast():
    while True:
        safe_call("recent_trades", recent_trades, symbol="BTCUSDT", limit=5)
        safe_call("trade_rate", trade_rate, symbol="BTCUSDT", window_seconds=60)
        time.sleep(FAST_POLL_SECONDS)


def poll_slow():
    while True:
        safe_call("price", price, symbol="BTCUSDT", change_window_seconds=3600)
        safe_call("volume", volume, symbol="BTCUSDT")
        safe_call("alerts", alerts, symbol="BTCUSDT", window_seconds=300)
        time.sleep(SLOW_POLL_SECONDS)


def poll_chart():
    while True:
        safe_call("price_history", price_history, symbol="BTCUSDT", window_minutes=15)
        time.sleep(CHART_POLL_SECONDS)


@app.on_event("startup")
def start_market_data_pollers():
    threading.Thread(target=poll_fast, daemon=True).start()
    threading.Thread(target=poll_slow, daemon=True).start()
    threading.Thread(target=poll_chart, daemon=True).start()


app.include_router(router, prefix="/api")

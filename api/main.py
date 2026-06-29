import threading
import time

from fastapi import FastAPI
from .routes import router, alerts, price, recent_trades, volume

app = FastAPI(title="API Dashboard Crypto")

MARKET_DATA_POLL_SECONDS = 3


def poll_market_data():
    while True:
        try:
            recent_trades(symbol="BTCUSDT", limit=5)
            price(symbol="BTCUSDT", change_window_seconds=3600)
            volume(symbol="BTCUSDT")
            alerts(symbol="BTCUSDT", window_seconds=300)
        except Exception as exc:
            print(f"poll_market_data error: {exc}")

        time.sleep(MARKET_DATA_POLL_SECONDS)


@app.on_event("startup")
def start_market_data_poller():
    threading.Thread(target=poll_market_data, daemon=True).start()


app.include_router(router, prefix="/api")

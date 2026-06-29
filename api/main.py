import threading
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router, price, recent_trades, volume

app = FastAPI(title="API Dashboard Crypto")

MARKET_DATA_POLL_SECONDS = 3


def poll_market_data():
    while True:
        try:
            recent_trades(symbol="BTCUSDT", limit=10)
            price(symbol="BTCUSDT", change_window_seconds=3600)
            volume(symbol="BTCUSDT")
        except Exception as exc:
            print(f"poll_market_data error: {exc}")

        time.sleep(MARKET_DATA_POLL_SECONDS)


@app.on_event("startup")
def start_market_data_poller():
    threading.Thread(target=poll_market_data, daemon=True).start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:5173",
        # "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://10.101.11.149:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


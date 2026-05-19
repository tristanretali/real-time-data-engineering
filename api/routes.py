from fastapi import APIRouter, Request, Query
from datetime import datetime, timezone

from .socketio_event import (
    emit_recent_trades,
    emit_volume,
    save_recent_trades_snapshot,
    save_volume_snapshot,
)
from .database import trades_collection

router = APIRouter()


@router.get("/recent_trades")
def recent_trades(
    symbol: str = Query("BTCUSDT"),
    limit: int = Query(5, ge=1, le=50),
):
    trades = list(
        trades_collection.find(
            {"symbol": symbol},
            {
                "_id": 1,
                "price": 1,
                "quantity": 1,
                "symbol": 1,
                "trade_time": 1,
            },
        )
        .sort("trade_time", -1)
        .limit(limit)
    )

    for trade in trades:
        trade["_id"] = str(trade["_id"])

        amount = trade["price"] * trade["quantity"]
        trade["amount"] = round(amount, 2)

        timestamp = trade.get("trade_time")
        dt = datetime.fromtimestamp(float(timestamp) / 1000.0, tz=timezone.utc)
        trade["trade_time_iso"] = dt.isoformat()

    save_recent_trades_snapshot(trades)
    emit_recent_trades(trades)

    return {"recent_trades": trades}


@router.get("/volume")
def volume(
    symbol: str = Query("BTCUSDT"),
    window_seconds: int = Query(120, ge=10, le=3600),
):
    # Calcul de la fenêtre de temps
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    since_ms = now_ms - (window_seconds * 1000)

    trades = list(
        trades_collection.find(
            {
                "symbol": symbol,
                "trade_time": {"$gte": since_ms},
            }
        )
    )

    volume_amount = 0.0
    for trade in trades:
        volume_amount += float(trade.get("price", 0)) * float(trade.get("quantity", 0))

    volume = {
        "window_minutes": window_seconds // 60,
        "total_volume_usd": round(volume_amount, 2),
        "count": len(trades),
    }

    save_volume_snapshot(volume)
    emit_volume(volume)

    return volume

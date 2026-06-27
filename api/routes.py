from fastapi import APIRouter, Request, Query
from datetime import datetime, timezone

from .socketio_event import (
    emit_recent_trades,
    emit_volume,
    save_recent_trades_snapshot,
    save_volume_snapshot,
    save_price_snapshot,
    emit_price,
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

    pipeline = [
        {
            "$match": {
                "symbol": symbol,
                "trade_time": {"$gte": since_ms},
            }
        },
        {
            "$group": {
                "_id": None,
                "total_volume_usd": {
                    "$sum": {
                        "$multiply": [
                            {"$toDouble": "$price"},
                            {"$toDouble": "$quantity"},
                        ]
                    }
                },
                "count": {"$sum": 1},
            }
        },
    ]

    result = list(trades_collection.aggregate(pipeline))
    summary = result[0] if result else {"total_volume_usd": 0, "count": 0}

    volume = {
        "window_minutes": window_seconds // 60,
        "total_volume_usd": round(float(summary["total_volume_usd"]), 2),
        "count": int(summary["count"]),
    }

    save_volume_snapshot(volume)
    emit_volume(volume)

    return volume


@router.get("/price")
def price(
    symbol: str = Query("BTCUSDT"),
    change_window_seconds: int = Query(3600, ge=60, le=86400),  # défaut 1h
):

    current_trade = trades_collection.find_one(
        {"symbol": symbol}, sort=[("trade_time", -1)]
    )

    if not current_trade:
        price_data = {
            "symbol": symbol,
            "current_price": 0.0,
            "change_percent": 0.0,
            "window_minutes": change_window_seconds // 60,
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        }

        save_price_snapshot(price_data)
        emit_price(price_data)

        return price_data

    current_price = float(current_trade.get("price", 0))
    current_time = int(current_trade.get("trade_time", 0))

    # Prix il y a X secondes
    since_ms = current_time - (change_window_seconds * 1000)
    old_trade = trades_collection.find_one(
        {
            "symbol": symbol,
            "trade_time": {"$lte": since_ms},
        },
        sort=[("trade_time", -1)],
    )

    if not old_trade:
        price_change_percent = 0.0

    else:
        old_price = float(old_trade.get("price", 0))
        price_change_percent = (
            ((current_price - old_price) / old_price * 100) if old_price != 0 else 0
        )

    price_data = {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "change_percent": round(price_change_percent, 2),
        "window_minutes": change_window_seconds // 60,
        "timestamp": current_time,
    }

    save_price_snapshot(price_data)
    emit_price(price_data)
    return price_data

from fastapi import APIRouter, Query
from datetime import datetime, timezone

from .socketio_event import (
    emit_recent_trades,
    emit_volume,
    save_recent_trades_snapshot,
    save_volume_snapshot,
    save_price_snapshot,
    emit_price,
    save_alerts_snapshot,
    emit_alerts,
    save_trade_rate_snapshot,
    emit_trade_rate,
    save_price_history_snapshot,
    emit_price_history,
)
from .database import trades_collection

router = APIRouter()
VOLUME_WINDOWS_SECONDS = [60, 300, 900]
PRICE_HISTORY_BUCKET_MS = 60 * 1000


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
                "trade_id": 1,
                "price": 1,
                "quantity": 1,
                "symbol": 1,
                "trade_time": 1,
                "is_market_maker": 1,
            },
        )
        .sort("trade_time", -1)
        .limit(limit)
    )

    for trade in trades:
        trade["_id"] = str(trade["_id"])

        amount = trade["price"] * trade["quantity"]
        trade["amount"] = round(amount, 2)
        trade["price"] = round(trade["price"], 2)
        trade["quantity"] = round(trade["quantity"], 8)

        timestamp = trade.get("trade_time")
        dt = datetime.fromtimestamp(float(timestamp) / 1000.0, tz=timezone.utc)
        trade["trade_time_iso"] = dt.isoformat()

    save_recent_trades_snapshot(trades)
    emit_recent_trades(trades)

    return {"recent_trades": trades}


@router.get("/trade_rate")
def trade_rate(
    symbol: str = Query("BTCUSDT"),
    window_seconds: int = Query(10, ge=1, le=60),
):
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    since_ms = now_ms - (window_seconds * 1000)

    count = trades_collection.count_documents(
        {"symbol": symbol, "trade_time": {"$gte": since_ms}}
    )

    payload = {
        "symbol": symbol,
        "window_seconds": window_seconds,
        "count": count,
        "trades_per_second": round(count / window_seconds, 2),
    }

    save_trade_rate_snapshot(payload)
    emit_trade_rate(payload)

    return payload


@router.get("/price_history")
def price_history(
    symbol: str = Query("BTCUSDT"),
    window_minutes: int = Query(15, ge=1, le=180),
):
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    since_ms = now_ms - (window_minutes * 60 * 1000)

    pipeline = [
        {"$match": {"symbol": symbol, "trade_time": {"$gte": since_ms}}},
        {
            "$group": {
                "_id": {
                    "$subtract": [
                        "$trade_time",
                        {"$mod": ["$trade_time", PRICE_HISTORY_BUCKET_MS]},
                    ]
                },
                "avg_price": {"$avg": {"$toDouble": "$price"}},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    buckets = list(trades_collection.aggregate(pipeline))

    points = [
        {
            "time": int(bucket["_id"]),
            "price": round(float(bucket["avg_price"]), 2),
        }
        for bucket in buckets
    ]

    payload = {
        "symbol": symbol,
        "window_minutes": window_minutes,
        "points": points,
    }

    save_price_history_snapshot(payload)
    emit_price_history(payload)

    return payload


@router.get("/volume")
def volume(symbol: str = Query("BTCUSDT")):
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    largest_window_seconds = max(VOLUME_WINDOWS_SECONDS)

    group_stage = {
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

    pipeline = [
        {
            "$match": {
                "symbol": symbol,
                "trade_time": {"$gte": now_ms - largest_window_seconds * 1000},
            }
        },
        {
            "$facet": {
                f"w_{window_seconds}": [
                    {
                        "$match": {
                            "trade_time": {"$gte": now_ms - window_seconds * 1000}
                        }
                    },
                    {"$group": group_stage},
                ]
                for window_seconds in VOLUME_WINDOWS_SECONDS
            }
        },
    ]

    result = list(trades_collection.aggregate(pipeline))
    facets = result[0] if result else {}

    windows = []
    for window_seconds in VOLUME_WINDOWS_SECONDS:
        bucket = facets.get(f"w_{window_seconds}") or []
        summary = bucket[0] if bucket else {"total_volume_usd": 0, "count": 0}
        windows.append(
            {
                "window_minutes": window_seconds // 60,
                "window_seconds": window_seconds,
                "total_volume_usd": round(float(summary["total_volume_usd"]), 2),
                "count": int(summary["count"]),
            }
        )

    payload = {"symbol": symbol, "windows": windows}

    save_volume_snapshot(payload)
    emit_volume(payload)

    return payload


@router.get("/price")
def price(
    symbol: str = Query("BTCUSDT"),
    change_window_seconds: int = Query(3600, ge=60, le=86400),
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


@router.get("/alerts")
def alerts(
    symbol: str = Query("BTCUSDT"),
    window_seconds: int = Query(60, ge=10, le=3600),
):
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    since_ms = now_ms - (window_seconds * 1000)

    recent_trades = list(
        trades_collection.find(
            {
                "symbol": symbol,
                "trade_time": {"$gte": since_ms},
            },
            {
                "_id": 0,
                "price": 1,
                "quantity": 1,
                "symbol": 1,
                "trade_time": 1,
            },
        ).sort("trade_time", -1)
    )

    alerts_list = []

    if not recent_trades:
        payload = {
            "symbol": symbol,
            "window_minutes": window_seconds // 60,
            "alerts": [],
            "count": 0,
        }
        save_alerts_snapshot(payload)
        emit_alerts(payload)
        return payload

    volumes = []
    quantities = []
    prices = []

    for trade in recent_trades:
        price = float(trade.get("price", 0))
        quantity = float(trade.get("quantity", 0))
        amount = price * quantity
        volumes.append(amount)
        quantities.append(quantity)
        prices.append(price)

    sorted_volumes = sorted(volumes)
    median_volume = sorted_volumes[len(sorted_volumes) // 2] if sorted_volumes else 0

    max_volume = max(volumes) if volumes else 0
    max_volume_idx = volumes.index(max_volume) if volumes and max_volume > 0 else -1
    max_volume_quantity = quantities[max_volume_idx] if max_volume_idx >= 0 else 0

    first_price = prices[-1] if prices else 0
    last_price = prices[0] if prices else 0

    price_change_percent = (
        ((last_price - first_price) / first_price) * 100
        if first_price not in (0, None)
        else 0
    )

    if max_volume >= median_volume * 10 and len(recent_trades) >= 2:
        multiplier = round(max_volume / median_volume, 0) if median_volume > 0 else 0
        alerts_list.append(
            {
                "type": "volume_anormal",
                "severity": "high",
                "detail": f"{round(max_volume_quantity, 8)} BTC sur 1 trade — seuil x{int(multiplier)}",
            }
        )

    if abs(price_change_percent) >= 0.1:
        price_change = last_price - first_price
        direction = "+" if price_change >= 0 else "-"
        price_change_percent = (
            ((price_change) / first_price) * 100 if first_price not in (0, None) else 0
        )

        alerts_list.append(
            {
                "type": "rapid_price_change",
                "severity": "medium",
                "detail": f"{direction}{abs(round(price_change, 2))}$ ({round(price_change_percent, 2)}%)",
            }
        )

    payload = {
        "symbol": symbol,
        "window_minutes": window_seconds // 60,
        "count": len(recent_trades),
        "alerts": alerts_list,
    }

    save_alerts_snapshot(payload)
    emit_alerts(payload)

    return payload

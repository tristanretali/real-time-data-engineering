from fastapi import APIRouter, Query

from .constants import DEFAULT_SYMBOL, PRICE_HISTORY_BUCKET_MS, VOLUME_WINDOWS_SECONDS
from .database import trades_collection
from .socketio_event import publish
from .time_utils import ms_ago, ms_to_iso, now_ms

router = APIRouter()


@router.get("/recent_trades")
def recent_trades(
    symbol: str = Query(DEFAULT_SYMBOL),
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
        trade["trade_time_iso"] = ms_to_iso(timestamp)

    return publish("recent_trades", {"recent_trades": trades})


@router.get("/trade_rate")
def trade_rate(
    symbol: str = Query(DEFAULT_SYMBOL),
    window_seconds: int = Query(10, ge=1, le=60),
):
    since_ms = ms_ago(now_ms(), window_seconds)

    count = trades_collection.count_documents(
        {"symbol": symbol, "trade_time": {"$gte": since_ms}}
    )

    payload = {
        "symbol": symbol,
        "window_seconds": window_seconds,
        "count": count,
        "trades_per_second": round(count / window_seconds, 2),
    }

    return publish("trade_rate", payload)


@router.get("/price_history")
def price_history(
    symbol: str = Query(DEFAULT_SYMBOL),
    window_minutes: int = Query(15, ge=1, le=180),
):
    since_ms = ms_ago(now_ms(), window_minutes * 60)

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

    return publish("price_history", payload)


@router.get("/volume")
def volume(symbol: str = Query(DEFAULT_SYMBOL)):
    current_ms = now_ms()
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
                "trade_time": {"$gte": ms_ago(current_ms, largest_window_seconds)},
            }
        },
        {
            "$facet": {
                f"w_{window_seconds}": [
                    {
                        "$match": {
                            "trade_time": {"$gte": ms_ago(current_ms, window_seconds)}
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

    return publish("volume", payload)


@router.get("/price")
def price(
    symbol: str = Query(DEFAULT_SYMBOL),
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
            "timestamp": now_ms(),
        }
        return publish("price", price_data)

    current_price = float(current_trade.get("price", 0))
    current_time = int(current_trade.get("trade_time", 0))

    since_ms = ms_ago(current_time, change_window_seconds)
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

    return publish("price", price_data)


@router.get("/alerts")
def alerts(
    symbol: str = Query(DEFAULT_SYMBOL),
    window_seconds: int = Query(60, ge=10, le=3600),
):
    since_ms = ms_ago(now_ms(), window_seconds)

    trades = list(
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

    if not trades:
        payload = {
            "symbol": symbol,
            "window_minutes": window_seconds // 60,
            "alerts": [],
            "count": 0,
        }
        return publish("alerts", payload)

    volumes = []
    quantities = []
    prices = []

    for trade in trades:
        trade_price = float(trade.get("price", 0))
        quantity = float(trade.get("quantity", 0))
        amount = trade_price * quantity
        volumes.append(amount)
        quantities.append(quantity)
        prices.append(trade_price)

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

    alerts_list = []

    if max_volume >= median_volume * 10 and len(trades) >= 2:
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
        "count": len(trades),
        "alerts": alerts_list,
    }

    return publish("alerts", payload)

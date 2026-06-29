from fastapi import APIRouter, Request, Query
from datetime import datetime, timezone

from .socketio_event import emit_recent_trades
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

    emit_recent_trades(trades)

    return {"recent_trades": trades}

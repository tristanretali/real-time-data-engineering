import { Zap } from "lucide-react";

export function RecentTrades({ trades }) {
  return (
    <aside className="card">
      <div className="panel-title">
        <h2>
          <Zap size={18} /> Trades récents
        </h2>
      </div>

      <div className="trade-list">
        {trades.length === 0 && <p>Aucun trade pour le moment.</p>}

        {trades.map((trade) => (
          <div
            className={`trade-row ${trade.anomaly ? "anomaly" : ""}`}
            key={trade.id}
          >
            <strong className={trade.tone}>{trade.price}</strong>
            <strong>{trade.amount}</strong>
            <span>Binance - {trade.symbol}</span>
            <small>{trade.time}</small>
          </div>
        ))}
      </div>

      <div className="legend">
        <span>
          <i className="dot danger"></i>Market maker (déjà dans le carnet)
        </span>
        <span>
          <i className="dot success"></i>Taker (exécuté immédiatement)
        </span>
      </div>
    </aside>
  );
}

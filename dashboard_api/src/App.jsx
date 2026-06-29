import { useEffect, useMemo, useState } from "react";
import { io } from "socket.io-client";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Database,
  SlidersHorizontal,
  Zap,
} from "lucide-react";

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || "http://localhost:8000";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

const quantityFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 8,
});

const compactCurrencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 2,
});

const initialState = {
  connected: false,
  trades: [],
  price: null,
  volume: null,
  alerts: [],
  alertsWindowMinutes: 0,
};

function formatTradeTime(value) {
  if (!value) return "--:--:--";

  const date = typeof value === "number" ? new Date(value) : new Date(value);

  return date.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatTrade(trade, index) {
  const quantity = Number(trade.quantity || 0);
  const price = Number(trade.price || 0);
  const amount = Number(trade.amount || price * quantity);

  return {
    id: String(trade.trade_id || trade._id || index),
    price: currencyFormatter.format(price),
    amount: `${quantityFormatter.format(quantity)} BTC`,
    time: formatTradeTime(trade.trade_time_iso || trade.trade_time),
    tone: trade.is_market_maker ? "negative" : "positive",
    anomaly: amount > 100000,
    symbol: trade.symbol || "BTCUSDT",
  };
}

function RecentTrades({ trades }) {
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
            <strong className={trade.tone}>
              {trade.price}
            </strong>
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

const ALERT_LABELS = {
  volume_anormal: "Volume anormal détecté",
  rapid_price_change: "Variation de prix rapide",
};

const SEVERITY_DOT_CLASS = {
  high: "danger",
  medium: "warning",
  low: "success",
};

function AlertsPanel({ alerts }) {
  return (
    <article className="card">
      <div className="panel-title">
        <h2>
          <AlertTriangle size={18} /> Alertes temps réel
        </h2>
      </div>

      <div className="alert-list">
        {alerts.length === 0 && <p>Aucune alerte détectée.</p>}

        {alerts.map((alert, index) => (
          <div className="alert-row" key={`${alert.type || "alert"}-${index}`}>
            <i className={`dot ${SEVERITY_DOT_CLASS[alert.severity] || "info"}`}></i>
            <strong>{ALERT_LABELS[alert.type] || alert.type || "Alerte"}</strong>
            <span>{alert.detail || "Aucun détail"}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

function formatWindowLabel(windowSeconds) {
  if (windowSeconds < 60) return `${windowSeconds}s`;
  if (windowSeconds < 3600) return `${windowSeconds / 60} min`;
  return `${windowSeconds / 3600} h`;
}

function VolumePanel({ volume }) {
  const windows = volume?.windows || [];

  return (
    <article className="card">
      <div className="panel-title">
        <h2>
          <BarChart3 size={18} /> Volume par fenêtre
        </h2>
      </div>

      {windows.length === 0 && <p>Aucune donnée de volume pour le moment.</p>}

      <div className="volume-list">
        {windows.map((window) => (
          <div className="volume-row" key={window.window_seconds}>
            <span>{formatWindowLabel(window.window_seconds)}</span>
            <b className="btc" style={{ "--width": "100%" }}></b>
            <strong>
              {compactCurrencyFormatter.format(Number(window.total_volume_usd || 0))}
            </strong>
          </div>
        ))}
      </div>
    </article>
  );
}

function PriceChartPlaceholder() {
  return (
    <article className="card chart-panel">
      <div className="panel-title">
        <h2>
          <Activity size={18} /> Prix BTC/USDT — Fenêtre glissante
        </h2>
      </div>

      <div className="chart-wrap chart-placeholder">
        <p>Courbe à venir</p>
      </div>
    </article>
  );
}

function PipelineHealth({ connected }) {
  const rows = [
    [
      "Socket.IO",
      connected ? "connecté" : "déconnecté",
      connected ? "positive" : "warning",
    ],
    ["Base de données", "MongoDB", "positive"],
    ["Pipeline", "Binance → Kafka → MongoDB", "positive"],
    ["Dashboard", "React actif", "positive"],
  ];

  return (
    <article className="card">
      <div className="panel-title">
        <h2>
          <Database size={18} /> Pipeline — Santé système
        </h2>
      </div>

      <div className="health-list">
        {rows.map(([label, value, tone]) => (
          <div key={label}>
            <span>{label}</span>
            <strong className={tone}>{value}</strong>
          </div>
        ))}
      </div>
    </article>
  );
}

function App() {
  const [dashboard, setDashboard] = useState(initialState);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      reconnection: true,
    });

    socket.on("connect_error", (error) => {
      console.error("Socket connect_error:", error.message);
    });

    socket.on("server_ready", (data) => {
      console.log(data);
    });

    socket.on("connect", () => {
      setDashboard((state) => ({ ...state, connected: true }));
    });

    socket.on("disconnect", () => {
      setDashboard((state) => ({ ...state, connected: false }));
    });

    socket.on("recent_trades", (data) => {
      const trades = (data?.recent_trades || []).map(formatTrade);
      setDashboard((state) => ({ ...state, trades }));
    });

    socket.on("price", (data) => {
      setDashboard((state) => ({ ...state, price: data }));
    });

    socket.on("volume", (data) => {
      setDashboard((state) => ({ ...state, volume: data }));
    });

    socket.on("alerts", (data) => {
      setDashboard((state) => ({
        ...state,
        alerts: data?.alerts || [],
        alertsWindowMinutes: data?.window_minutes || 0,
      }));
    });

    return () => socket.disconnect();
  }, []);

  const currentPrice = useMemo(() => {
    const price = Number(dashboard.price?.current_price || 0);
    return currencyFormatter.format(price);
  }, [dashboard.price]);

  const priceMeta = useMemo(() => {
    const change = Number(dashboard.price?.change_percent || 0);
    return `${change >= 0 ? "+" : ""}${change.toFixed(2)}% vs ${
      dashboard.price?.window_minutes || 60
    } min`;
  }, [dashboard.price]);

  const priceTone = Number(dashboard.price?.change_percent || 0) >= 0
    ? "positive"
    : "negative";

  const headlineWindow = useMemo(() => {
    const windows = dashboard.volume?.windows || [];
    return (
      windows.find((window) => window.window_seconds === 300) || windows[0]
    );
  }, [dashboard.volume]);

  const volumeValue = useMemo(() => {
    return currencyFormatter.format(Number(headlineWindow?.total_volume_usd || 0));
  }, [headlineWindow]);

  const tradesPerSecond = useMemo(() => {
    const count = Number(headlineWindow?.count || 0);
    const seconds = Number(headlineWindow?.window_seconds || 1);
    return (count / seconds).toFixed(1);
  }, [headlineWindow]);

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <SlidersHorizontal size={26} />
          <h1>Crypto Market Monitor — Real-Time Pipeline</h1>
        </div>

        <div className="sources">
          <span className="source binance">Binance</span>
          <span className="live-dot"></span>
          <strong>{dashboard.connected ? "LIVE" : "OFFLINE"}</strong>
        </div>
      </header>

      <section className="kpi-grid">
        <article className="card kpi-card">
          <span>BTC/USDT — Prix actuel</span>
          <strong className={priceTone}>{currentPrice}</strong>
          <small className={priceTone}>{priceMeta}</small>
        </article>

        <article className="card kpi-card">
          <span>Volume</span>
          <strong>{volumeValue}</strong>
          <small>Volume sur {headlineWindow?.window_minutes || 0} min</small>
        </article>

        <article className="card kpi-card">
          <span>Trades / seconde</span>
          <strong className="positive">{tradesPerSecond}</strong>
          <small>Binance</small>
        </article>

        <article className="card kpi-card">
          <span>Anomalies détectées</span>
          <strong className="warning">{dashboard.alerts.length}</strong>
          <small>dernières {dashboard.alertsWindowMinutes} min</small>
        </article>
      </section>

      <section className="main-grid">
        <PriceChartPlaceholder />
        <RecentTrades trades={dashboard.trades} />
      </section>

      <section className="bottom-grid">
        <AlertsPanel alerts={dashboard.alerts} />
        <VolumePanel volume={dashboard.volume} />
        <PipelineHealth connected={dashboard.connected} />
      </section>

      <footer>
        Kafka topic: <strong>crypto.trades.raw</strong> — MongoDB — FastAPI —
        React
      </footer>
    </main>
  );
}

export default App;
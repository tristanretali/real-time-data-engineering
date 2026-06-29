import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Database,
  SlidersHorizontal,
  Zap,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

const quantityFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 8,
});

const defaultPriceSeries = [
  { time: "13:52", price: 67030, average: 67020 },
  { time: "13:55", price: 67070, average: 67050 },
  { time: "13:58", price: 67082, average: 67062 },
  { time: "14:01", price: 67045, average: 67078 },
  { time: "14:04", price: 67118, average: 67102 },
  { time: "14:07", price: 67162, average: 67124 },
];

const fallbackTrades = [];

function formatTradeTime(value) {
  if (!value) return "--:--:--";

  const date =
    typeof value === "number"
      ? new Date(value)
      : new Date(value);

  return date.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function mapApiTrade(trade, index) {
  const quantity = Number(trade.quantity || 0);
  const price = Number(trade.price || 0);
  const amount = Number(trade.amount || price * quantity);

  return {
    id: String(trade.trade_id || trade._id || index),
    price: currencyFormatter.format(price),
    market: `Binance - ${trade.symbol || "BTCUSDT"}`,
    amount: `${quantityFormatter.format(quantity)} BTC`,
    time: formatTradeTime(trade.trade_time_iso || trade.trade_time),
    tone: trade.is_market_maker ? "down" : "up",
    anomaly: amount > 100000,
  };
}

function KpiCard({ label, value, meta, tone }) {
  return (
    <article className="card kpi-card">
      <span>{label}</span>
      <strong className={tone}>{value}</strong>
      <small className={tone}>{meta}</small>
    </article>
  );
}





function PriceChart({ series }) {
  return (
    <article className="card chart-panel">
      <div className="panel-title">
        <h2>
          <Activity size={18} /> Prix BTC/USDT — 1 point toutes les 5 secondes
        </h2>
        <strong>Moy. mobile</strong>
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={series}
            margin={{ top: 20, right: 30, left: 10, bottom: 25 }}
          >
            <CartesianGrid stroke="rgba(255,255,255,0.08)" />

            <XAxis
              dataKey="time"
              tick={{ fill: "#9ca3af", fontSize: 12 }}
              axisLine={{ stroke: "#374151" }}
              tickLine={{ stroke: "#374151" }}
            />

            <YAxis
              domain={["auto", "auto"]}
              tick={{ fill: "#9ca3af", fontSize: 12 }}
              axisLine={{ stroke: "#374151" }}
              tickLine={{ stroke: "#374151" }}
              tickFormatter={(value) => `$${Number(value).toLocaleString("en-US")}`}
            />

            <Tooltip
              formatter={(value, name) => [
                `$${Number(value).toLocaleString("en-US")}`,
                name === "price" ? "Prix BTC" : "Moyenne mobile",
              ]}
              labelFormatter={(label) => `Heure : ${label}`}
              contentStyle={{
                background: "#111721",
                border: "1px solid #2b3444",
                borderRadius: "8px",
                color: "#eef3ff",
              }}
            />

            <Line
              type="monotone"
              dataKey="average"
              stroke="#e6bd47"
              strokeDasharray="5 6"
              strokeWidth={2}
              dot={{ r: 3 }}
            />

            <Line
              type="monotone"
              dataKey="price"
              stroke="#6596ff"
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}



function RecentTrades({ trades, status }) {
  return (
    <aside className="card">
      <div className="panel-title">
        <h2>
          <Zap size={18} /> Trades récents
        </h2>
        <span className={status === "API live" ? "positive" : ""}>
          {status}
        </span>
      </div>

      <div className="trade-list">
        {trades.length === 0 && <p>Aucun trade pour le moment.</p>}

        {trades.map((trade) => (
          <div
            className={`trade-row ${trade.anomaly ? "anomaly" : ""}`}
            key={trade.id}
          >
            <strong className={trade.tone === "up" ? "positive" : "negative"}>
              {trade.price}
            </strong>
            <strong>{trade.amount}</strong>
            <span>{trade.market}</span>
            <small>{trade.time}</small>
          </div>
        ))}
      </div>
    </aside>
  );
}

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
          <div className="alert-row" key={index}>
            <i className={`dot ${alert.severity || "info"}`}></i>
            <strong>{alert.type || "Alerte"}</strong>
            <span>{alert.detail}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

function VolumePanel({ volume }) {
  const total = Number(volume?.total_volume_usd || 0);
  const count = Number(volume?.count || 0);

  return (
    <article className="card">
      <div className="panel-title">
        <h2>
          <BarChart3 size={18} /> Volume par fenêtre
        </h2>
      </div>

      <div className="volume-list">
        <div className="volume-row">
          <span>{volume?.window_minutes || 0} min</span>
          <b className="btc" style={{ "--width": "80%" }}></b>
          <strong>{currencyFormatter.format(total)}</strong>
        </div>

        <div className="volume-row">
          <span>Trades</span>
          <b className="eth" style={{ "--width": "55%" }}></b>
          <strong>{count}</strong>
        </div>
      </div>
    </article>
  );
}


// function VolumePanel({ volume }) {

//   const one = volume?.oneMinute;
//   const five = volume?.fiveMinutes;
//   const fifteen = volume?.fifteenMinutes;

//   return (
//     <article className="card">
//       <div className="panel-title">
//         <h2>
//           <BarChart3 size={18} /> Volume par fenêtre
//         </h2>
//       </div>

//       <div className="volume-list">

//         <div className="volume-row">
//           <span>1 min</span>
//           <b className="btc" style={{ "--width": "35%" }}></b>
//           <strong>
//             {currencyFormatter.format(one?.total_volume_usd || 0)}
//           </strong>
//         </div>

//         <div className="volume-row">
//           <span>5 min</span>
//           <b className="btc" style={{ "--width": "70%" }}></b>
//           <strong>
//             {currencyFormatter.format(five?.total_volume_usd || 0)}
//           </strong>
//         </div>

//         <div className="volume-row">
//           <span>15 min</span>
//           <b className="btc" style={{ "--width": "100%" }}></b>
//           <strong>
//             {currencyFormatter.format(fifteen?.total_volume_usd || 0)}
//           </strong>
//         </div>

//         <div className="volume-row">
//           <span>Trades</span>
//           <b className="eth" style={{ "--width": "55%" }}></b>
//           <strong>{five?.count || 0}</strong>
//         </div>

//       </div>
//     </article>
//   );
// }


function PipelineHealth({ status }) {
  const rows = [
    ["API FastAPI", status === "API live" ? "connectée" : "indisponible", status === "API live" ? "positive" : "warning"],
    ["Base de données", "MongoDB", "positive"],
    ["WebSocket", "Binance", "positive"],
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
  const [tradeFeed, setTradeFeed] = useState(fallbackTrades);
  const [tradeStatus, setTradeStatus] = useState("chargement API");

  const [currentPrice, setCurrentPrice] = useState("$0.00");
  const [priceMeta, setPriceMeta] = useState("0.00% vs 1h");
  const [priceTone, setPriceTone] = useState("positive");

  const [volume, setVolume] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [priceSeries, setPriceSeries] = useState(defaultPriceSeries);

  async function refreshDashboard() {
    try {
      const [tradesRes, priceRes, volumeRes, alertsRes] =
        await Promise.allSettled([
          fetch(`${API_BASE_URL}/api/recent_trades?symbol=BTCUSDT&limit=6`),
          fetch(`${API_BASE_URL}/api/price?symbol=BTCUSDT&change_window_seconds=3600`),
          fetch(`${API_BASE_URL}/api/volume?symbol=BTCUSDT&window_seconds=300`),
      //     Promise.all([
      //     fetch(`${API_BASE_URL}/api/volume?symbol=BTCUSDT&window_seconds=60`),
      //     fetch(`${API_BASE_URL}/api/volume?symbol=BTCUSDT&window_seconds=300`),
      //     fetch(`${API_BASE_URL}/api/volume?symbol=BTCUSDT&window_seconds=900`)
      // ]),
          fetch(`${API_BASE_URL}/api/alerts?symbol=BTCUSDT&window_seconds=600`),
        ]);




      if (tradesRes.status === "fulfilled" && tradesRes.value.ok) {
        const data = await tradesRes.value.json();
        const trades = (data.recent_trades || []).map(mapApiTrade);
        setTradeFeed(trades);
        setTradeStatus("API live");
      } else {
        setTradeStatus("API indisponible");
      }

      if (priceRes.status === "fulfilled" && priceRes.value.ok) {
        const data = await priceRes.value.json();

        const price = Number(data.current_price || 0);
        const change = Number(data.change_percent || 0);

        setCurrentPrice(currencyFormatter.format(price));
        setPriceMeta(`${change >= 0 ? "+" : ""}${change.toFixed(2)}% vs 1h`);
        setPriceTone(change >= 0 ? "positive" : "negative");

        setPriceSeries((oldSeries) => {
          const now = new Date().toLocaleTimeString("fr-FR", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });

          const nextPoint = {
            time: now,
            price,
            average: price,
          };

          return [...oldSeries.slice(-20), nextPoint];
        });
      }

      if (volumeRes.status === "fulfilled" && volumeRes.value.ok) {
        const data = await volumeRes.value.json();
        setVolume(data);
      }

      if (alertsRes.status === "fulfilled" && alertsRes.value.ok) {
        const data = await alertsRes.value.json();
        setAlerts(data.alerts || []);
      }
    } catch {
      setTradeStatus("API indisponible");
    }
  }



useEffect(() => {
  refreshDashboard();

  const interval = setInterval(refreshDashboard, 5000);

  return () => clearInterval(interval);
}, []);



  const volumeValue = volume
    ? currencyFormatter.format(volume.total_volume_usd || 0)
    : "$0.00";

  const tradesPerSecond = volume
    ? (Number(volume.count || 0) / Number(volume.window_seconds || 300)).toFixed(1)
    : "0.0";

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <SlidersHorizontal size={26} />
          <h1>Crypto Market Monitor — Real-Time Pipeline</h1>
        </div>

        <div className="sources">
          <span className="source binance">Binance</span>
          <span className="source coinbase">Coinbase</span>
          <span className="live-dot"></span>
          <strong>LIVE</strong>
        </div>
      </header>

      <section className="ticker">
        <div>
          BTC/USDT{" "}
          <strong className={priceTone}>
            {currentPrice} {priceMeta}
          </strong>
        </div>
        <i></i>
        <div>
          Volume 5 min <strong>{volumeValue}</strong>
        </div>
        <i></i>
        <div>
          Alertes <strong className="warning">{alerts.length}</strong>
        </div>
      </section>

      <section className="kpi-grid">
        <KpiCard
          label="BTC/USDT — Prix actuel"
          value={currentPrice}
          meta={priceMeta}
          tone={priceTone}
        />

        <KpiCard
          label="Vol glissant 5 min"
          value={volumeValue}
          meta={`${volume?.count || 0} trades`}
        />

        <KpiCard
          label="Trades / seconde"
          value={tradesPerSecond}
          meta="Binance"
          tone="positive"
        />

        <KpiCard
          label="Anomalies détectées"
          value={alerts.length}
          meta="dernières 10 min"
          tone="warning"
        />
      </section>

      <section className="main-grid">
        <PriceChart series={priceSeries} />
        <RecentTrades trades={tradeFeed} status={tradeStatus} />
      </section>

      <section className="bottom-grid">
        <AlertsPanel alerts={alerts} />
        <VolumePanel volume={volume} />
        <PipelineHealth status={tradeStatus} />
      </section>

      <footer>
        Kafka topic: <strong>crypto.trades.raw</strong> — MongoDB — FastAPI —
        React — Recharts
      </footer>
    </main>
  );
}

export default App;
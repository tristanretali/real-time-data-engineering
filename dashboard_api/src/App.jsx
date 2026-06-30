import { useMemo } from "react";
import { SlidersHorizontal } from "lucide-react";

import { AlertsPanel } from "./components/AlertsPanel";
import { PipelineHealth } from "./components/PipelineHealth";
import { PriceChart } from "./components/PriceChart";
import { RecentTrades } from "./components/RecentTrades";
import { VolumePanel } from "./components/VolumePanel";
import { useDashboardSocket } from "./hooks/useDashboardSocket";
import { currencyFormatter } from "./utils/format";

const HEADLINE_VOLUME_WINDOW_SECONDS = 300;

function App() {
  const dashboard = useDashboardSocket();

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

  const priceTone =
    Number(dashboard.price?.change_percent || 0) >= 0 ? "positive" : "negative";

  const headlineWindow = useMemo(() => {
    const windows = dashboard.volume?.windows || [];
    return (
      windows.find((entry) => entry.window_seconds === HEADLINE_VOLUME_WINDOW_SECONDS) ||
      windows[0]
    );
  }, [dashboard.volume]);

  const volumeValue = useMemo(() => {
    return currencyFormatter.format(Number(headlineWindow?.total_volume_usd || 0));
  }, [headlineWindow]);

  const tradesPerSecond = Math.round(Number(dashboard.tradeRate?.trades_per_second || 0));

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
          <span>Volume sur {headlineWindow?.window_minutes || 0} min</span>
          <strong>{volumeValue}</strong>
        </article>

        <article className="card kpi-card">
          <span>Trades / seconde</span>
          <strong className="positive">{tradesPerSecond}</strong>
        </article>

        <article className="card kpi-card">
          <span>Anomalies détectées</span>
          <strong className="warning">{dashboard.alerts.length}</strong>
          <small>dernières {dashboard.alertsWindowMinutes} min</small>
        </article>
      </section>

      <section className="main-grid">
        <PriceChart points={dashboard.priceHistory} />
        <RecentTrades trades={dashboard.trades} />
      </section>

      <section className="bottom-grid">
        <AlertsPanel alerts={dashboard.alerts} />
        <VolumePanel volume={dashboard.volume} />
        <PipelineHealth
          connected={dashboard.connected}
          consumerGroup={dashboard.consumerGroup}
        />
      </section>
    </main>
  );
}

export default App;

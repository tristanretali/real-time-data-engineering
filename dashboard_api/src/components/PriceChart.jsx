import { Activity } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatMinuteLabel } from "../utils/format";

const MOVING_AVERAGE_WINDOW = 3;

function average(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function withMovingAverage(points) {
  return points.map((point, index) => {
    const windowStart = Math.max(0, index - MOVING_AVERAGE_WINDOW + 1);
    const window = points.slice(windowStart, index + 1);
    return {
      ...point,
      average: Math.round(average(window.map((p) => p.price)) * 100) / 100,
    };
  });
}

export function PriceChart({ points }) {
  const data = withMovingAverage(points).map((point) => ({
    time: formatMinuteLabel(point.time),
    price: point.price,
    average: point.average,
  }));

  return (
    <article className="card chart-panel">
      <div className="panel-title">
        <h2>
          <Activity size={18} /> Prix BTC/USDT — Fenêtre glissante 15 min
        </h2>
      </div>

      <div className="chart-wrap">
        {data.length === 0 ? (
          <div className="chart-placeholder">
            <p>Pas encore assez de données.</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
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
                  name === "price" ? "Prix BTC" : "Moy. mobile",
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
                dot={{ r: 3 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {data.length > 0 && (
        <div className="legend">
          <span>
            <i className="line blue-line"></i>Prix BTC
          </span>
          <span>
            <i className="line gold-line"></i>Moy. mobile
          </span>
        </div>
      )}
    </article>
  );
}

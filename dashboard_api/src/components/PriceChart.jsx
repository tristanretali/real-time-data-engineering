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

export function PriceChart({ points }) {
  const data = points.map((point) => ({
    time: formatMinuteLabel(point.time),
    price: point.price,
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
                formatter={(value) => [
                  `$${Number(value).toLocaleString("en-US")}`,
                  "Prix BTC",
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
    </article>
  );
}

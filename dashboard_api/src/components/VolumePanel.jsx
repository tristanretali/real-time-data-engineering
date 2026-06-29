import { BarChart3 } from "lucide-react";

import { compactCurrencyFormatter, formatWindowLabel } from "../utils/format";

export function VolumePanel({ volume }) {
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
        {windows.map((entry) => (
          <div className="volume-row" key={entry.window_seconds}>
            <span>{formatWindowLabel(entry.window_seconds)}</span>
            <b className="btc" style={{ "--width": "100%" }}></b>
            <strong>
              {compactCurrencyFormatter.format(Number(entry.total_volume_usd || 0))}
            </strong>
          </div>
        ))}
      </div>
    </article>
  );
}

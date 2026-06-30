import { BarChart3 } from "lucide-react";

import { compactCurrencyFormatter, formatWindowLabel } from "../utils/format";

export function VolumePanel({ volume }) {
  const windows = volume?.windows || [];
  const maxVolume = Math.max(0, ...windows.map((entry) => entry.total_volume_usd || 0));

  return (
    <article className="card">
      <div className="panel-title">
        <h2>
          <BarChart3 size={18} /> Volume par fenêtre
        </h2>
      </div>

      {windows.length === 0 && <p>Aucune donnée de volume pour le moment.</p>}

      <div className="volume-list">
        {windows.map((entry) => {
          const widthPercent =
            maxVolume > 0 ? ((entry.total_volume_usd || 0) / maxVolume) * 100 : 0;

          return (
            <div className="volume-row" key={entry.window_seconds}>
              <span>{formatWindowLabel(entry.window_seconds)}</span>
              <b className="btc" style={{ "--width": `${widthPercent}%` }}></b>
              <strong>
                {compactCurrencyFormatter.format(Number(entry.total_volume_usd || 0))}
              </strong>
            </div>
          );
        })}
      </div>
    </article>
  );
}

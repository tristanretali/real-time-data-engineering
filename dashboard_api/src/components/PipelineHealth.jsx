import { Database } from "lucide-react";

export function PipelineHealth({ connected, consumerGroup }) {
  const allWorkersActive =
    consumerGroup.total > 0 && consumerGroup.active === consumerGroup.total;

  const rows = [
    [
      "Socket.IO",
      connected ? "connecté" : "déconnecté",
      connected ? "positive" : "warning",
    ],
    ["Base de données", "MongoDB", "positive"],
    ["Pipeline", "Binance → Kafka → MongoDB", "positive"],
    [
      "Consumer group",
      `${consumerGroup.active} / ${consumerGroup.total} actifs`,
      allWorkersActive ? "positive" : "warning",
    ],
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

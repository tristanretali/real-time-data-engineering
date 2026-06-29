import { Database } from "lucide-react";

export function PipelineHealth({ connected }) {
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

import { AlertTriangle } from "lucide-react";

import { ALERT_LABELS, SEVERITY_DOT_CLASS } from "../constants";

export function AlertsPanel({ alerts }) {
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

export const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || "http://localhost:8000";

export const ALERT_LABELS = {
  volume_anormal: "Volume anormal détecté",
  rapid_price_change: "Variation de prix rapide",
};

export const SEVERITY_DOT_CLASS = {
  high: "danger",
  medium: "warning",
  low: "success",
};

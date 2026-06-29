const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function handleResponse(res) {
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${txt}`);
  }
  return res.json();
}

function buildUrl(path, params = {}) {
  const url = new URL(`${API_BASE_URL}${path}`);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) {
      url.searchParams.set(k, String(v));
    }
  });
  return url.toString();
}

export function fetchRecentTrades(symbol = "BTCUSDT", limit = 6) {
  return fetch(buildUrl("/api/recent_trades", { symbol, limit })).then(handleResponse);
}

export function fetchPrice(symbol = "BTCUSDT", change_window_seconds = 3600) {
  return fetch(buildUrl("/api/price", { symbol, change_window_seconds })).then(handleResponse);
}

export function fetchVolume(symbol = "BTCUSDT", window_seconds = 120) {
  return fetch(buildUrl("/api/volume", { symbol, window_seconds })).then(handleResponse);
}

export function fetchAlerts(symbol = "BTCUSDT", window_seconds = 60) {
  return fetch(buildUrl("/api/alerts", { symbol, window_seconds })).then(handleResponse);
}
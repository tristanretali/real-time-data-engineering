export const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

export const quantityFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 8,
});

export const compactCurrencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 2,
});

export function formatTradeTime(value) {
  if (!value) return "--:--:--";

  const date = new Date(value);

  return date.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatMinuteLabel(timeMs) {
  if (!timeMs) return "--:--";
  return new Date(timeMs).toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatWindowLabel(windowSeconds) {
  if (windowSeconds < 60) return `${windowSeconds}s`;
  if (windowSeconds < 3600) return `${windowSeconds / 60} min`;
  return `${windowSeconds / 3600} h`;
}

export function formatTrade(trade, index) {
  const quantity = Number(trade.quantity || 0);
  const price = Number(trade.price || 0);
  const amount = Number(trade.amount || price * quantity);

  return {
    id: String(trade.trade_id || trade._id || index),
    price: currencyFormatter.format(price),
    amount: `${quantityFormatter.format(quantity)} BTC`,
    time: formatTradeTime(trade.trade_time_iso || trade.trade_time),
    tone: trade.is_market_maker ? "negative" : "positive",
    anomaly: amount > 100000,
    symbol: trade.symbol || "BTCUSDT",
  };
}

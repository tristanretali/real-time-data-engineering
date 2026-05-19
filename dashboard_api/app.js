const trades = [
  { price: 67284.5, pair: "Binance · BTC/USDT", amount: "0.183 BTC", time: "14:22:03.481", side: "buy" },
  { price: 67281.0, pair: "Binance · BTC/USDT", amount: "0.042 BTC", time: "14:22:03.299", side: "sell" },
  { price: 67271.0, pair: "Coinbase · BTC-USD", amount: "1.200 BTC", time: "14:22:02.914", side: "buy" },
  { price: 67244.0, pair: "Binance · BTC/USDT", amount: "18.50 BTC", time: "14:22:01.003", side: "sell", anomaly: true },
  { price: 67268.0, pair: "Coinbase · BTC-USD", amount: "0.320 BTC", time: "14:22:00.771", side: "buy" },
  { price: 67275.5, pair: "Binance · ETH/USDT", amount: "2.100 ETH", time: "14:21:59.580", side: "buy" },
];

const formatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
});

const compactFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function renderTrades() {
  const feed = document.getElementById("trade-feed");

  feed.innerHTML = trades
    .map((trade) => {
      const tone = trade.side === "sell" ? "negative" : "positive";
      const anomaly = trade.anomaly ? " anomaly" : "";

      return `
        <div class="trade${anomaly}">
          <strong class="${tone}">${formatter.format(trade.price)}</strong>
          <strong>${trade.amount}</strong>
          <span>${trade.pair}</span>
          <small>${trade.time}</small>
        </div>
      `;
    })
    .join("");
}

function tick() {
  const price = 67284 + Math.random() * 22 - 8;
  const tradesPerSecond = 36 + Math.random() * 5;
  const now = new Date();

  document.getElementById("btc-price").textContent = compactFormatter.format(price);
  document.getElementById("trades-sec").textContent = tradesPerSecond.toFixed(1);
  document.getElementById("updated-at").textContent = now.toISOString().slice(11, 19) + " UTC";
}

renderTrades();
tick();
setInterval(tick, 1500);

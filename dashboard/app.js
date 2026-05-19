const socketHost = window.location.hostname === "localhost" ? "127.0.0.1" : window.location.hostname;
const socketUrl = `${window.location.protocol}//${socketHost}:8000`;

const socket = window.io(socketUrl, {
  transports: ["websocket", "polling"],
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 8000,
});

const state = {
  services: new Map(),
  events: [],
};

const els = {
  socketStatus: document.getElementById("socket-status"),
  socketMeta: document.getElementById("socket-meta"),
  summaryStatus: document.getElementById("summary-status"),
  summaryMeta: document.getElementById("summary-meta"),
  priceMeta: document.getElementById("price-meta"),
  healthyCount: document.getElementById("healthy-count"),
  healthyTotal: document.getElementById("healthy-total"),
  degradedTotal: document.getElementById("degraded-total"),
  downTotal: document.getElementById("down-total"),
  serviceGrid: document.getElementById("service-grid"),
  eventFeed: document.getElementById("event-feed"),
  serviceCountChip: document.getElementById("service-count-chip"),
};

function formatTime(ms) {
  return new Date(ms).toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function pushEvent(title, detail, status = "healthy") {
  state.events.unshift({ title, detail, status, time: new Date().toLocaleTimeString() });
  state.events = state.events.slice(0, 12);
  renderEvents();
}

function formatStatus(service) {
  const colors = {
    healthy: "online",
    degraded: "warn",
    down: "offline",
  };
  return colors[service.status] || "warn";
}

function renderServices() {
  const services = [...state.services.values()].sort((a, b) => a.service.localeCompare(b.service));
  const totals = services.reduce(
    (acc, service) => {
      acc[service.status] = (acc[service.status] || 0) + 1;
      return acc;
    },
    { healthy: 0, degraded: 0, down: 0 }
  );

  els.healthyCount.textContent = String(totals.healthy);
  els.healthyTotal.textContent = String(totals.healthy);
  els.degradedTotal.textContent = String(totals.degraded);
  els.downTotal.textContent = String(totals.down);
  els.serviceCountChip.textContent = String(services.length);

  els.summaryStatus.textContent =
    totals.down > 0 ? "Attention required" : totals.degraded > 0 ? "Degraded" : "Healthy";
  els.summaryStatus.className =
    totals.down > 0 ? "status-value offline" : totals.degraded > 0 ? "status-value warn" : "status-value online";
  els.summaryMeta.textContent = `${totals.healthy} healthy, ${totals.degraded} degraded, ${totals.down} down`;

  els.serviceGrid.innerHTML = services
    .map(
      (service) => `
        <div class="service-card">
          <div class="service-head">
            <strong>${service.service}</strong>
            <span class="chip ${formatStatus(service)}">${service.status}</span>
          </div>
          <div class="trade-meta">${service.message}</div>
          <div class="trade-meta">${service.age_seconds !== undefined ? `Age ${service.age_seconds}s` : formatTime(service.timestamp)}</div>
        </div>
      `
    )
    .join("");
}

function renderEvents() {
  els.eventFeed.innerHTML = state.events
    .map(
      (item) => `
        <div class="event-item">
          <div class="trade-title">${item.title}</div>
          <div class="trade-meta">${item.detail}</div>
          <div class="trade-meta">${item.time}</div>
        </div>
      `
    )
    .join("");
}

socket.on("connect", () => {
  els.socketStatus.textContent = "Connected";
  els.socketStatus.className = "status-value online";
  els.socketMeta.textContent = `Socket ID ${socket.id}`;
  pushEvent("Socket.IO", "Connected to orchestration backend");
});

socket.on("disconnect", () => {
  els.socketStatus.textContent = "Disconnected";
  els.socketStatus.className = "status-value offline";
  els.socketMeta.textContent = "Waiting for reconnect";
  pushEvent("Socket.IO", "Disconnected from backend", "down");
});

socket.on("server_ready", (payload) => {
  pushEvent("Backend", payload.message);
});

socket.on("service_health", (payload) => {
  state.services.set(payload.service, payload);
  renderServices();
  pushEvent(payload.service, `${payload.status} - ${payload.message}`);
});

socket.on("orchestration_snapshot", (snapshot) => {
  snapshot.services.forEach((service) => state.services.set(service.service, service));
  renderServices();
  pushEvent("Monitor", `Snapshot refreshed: ${snapshot.summary.healthy}/${snapshot.summary.total} healthy`);
});

socket.on("connect_error", (error) => {
  els.socketStatus.textContent = "Error";
  els.socketStatus.className = "status-value offline";
  els.socketMeta.textContent = `${error.message || "Unable to connect"} (${socketUrl})`;
  pushEvent("Socket.IO", `Connection error to ${socketUrl}`, "down");
});

pushEvent("Dashboard", "Ready to monitor orchestration health");
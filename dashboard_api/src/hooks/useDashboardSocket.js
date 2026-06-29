import { useEffect, useState } from "react";
import { io } from "socket.io-client";

import { SOCKET_URL } from "../constants";
import { formatTrade } from "../utils/format";

const initialState = {
  connected: false,
  trades: [],
  price: null,
  volume: null,
  tradeRate: null,
  priceHistory: [],
  alerts: [],
  alertsWindowMinutes: 0,
};

const EVENT_REDUCERS = {
  recent_trades: (state, data) => ({
    ...state,
    trades: (data?.recent_trades || []).map(formatTrade),
  }),
  price: (state, data) => ({ ...state, price: data }),
  volume: (state, data) => ({ ...state, volume: data }),
  trade_rate: (state, data) => ({ ...state, tradeRate: data }),
  price_history: (state, data) => ({
    ...state,
    priceHistory: data?.points || [],
  }),
  alerts: (state, data) => ({
    ...state,
    alerts: data?.alerts || [],
    alertsWindowMinutes: data?.window_minutes || 0,
  }),
};

export function useDashboardSocket() {
  const [dashboard, setDashboard] = useState(initialState);

  useEffect(() => {
    const socket = io(SOCKET_URL, { reconnection: true });

    socket.on("connect_error", (error) => {
      console.error("Socket connect_error:", error.message);
    });

    socket.on("server_ready", (data) => {
      console.log(data);
    });

    socket.on("connect", () => {
      setDashboard((state) => ({ ...state, connected: true }));
    });

    socket.on("disconnect", () => {
      setDashboard((state) => ({ ...state, connected: false }));
    });

    Object.entries(EVENT_REDUCERS).forEach(([event, reducer]) => {
      socket.on(event, (data) => setDashboard((state) => reducer(state, data)));
    });

    return () => socket.disconnect();
  }, []);

  return dashboard;
}

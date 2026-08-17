"use client";

import * as React from "react";

import { api, type Quote } from "@/lib/api";

interface UseMarketStreamOptions {
  symbols: string[];
  exchange: string;
  token: string | null;
  /** Fallback polling interval (ms) used when WebSocket is unavailable. */
  pollInterval?: number;
  onError?: (message: string) => void;
}

interface UseMarketStreamResult {
  quotes: Quote[];
  mode: "idle" | "live" | "polling";
  refresh: () => Promise<void>;
}

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_BASE_MS = 1000;

/**
 * Streams market quotes over a WebSocket, transparently falling back to
 * REST polling when the connection cannot be established or keeps dropping.
 * Live (provider) data is indistinguishable from mock data on the client
 * except via each quote's `is_mock`/`source` fields.
 */
export function useMarketStream({
  symbols,
  exchange,
  token,
  pollInterval = 3000,
  onError,
}: UseMarketStreamOptions): UseMarketStreamResult {
  const [quotes, setQuotes] = React.useState<Quote[]>([]);
  const [mode, setMode] = React.useState<"idle" | "live" | "polling">("idle");
  const wsRef = React.useRef<WebSocket | null>(null);
  const pollRef = React.useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimer = React.useRef<ReturnType<typeof setTimeout> | null>(
    null
  );
  const reconnectAttempts = React.useRef(0);
  const fallbackScheduled = React.useRef(false);
  const connectRef = React.useRef<() => void>(() => {});
  const stateRef = React.useRef({ symbols, exchange, token });
  const onErrorRef = React.useRef(onError);

  React.useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  React.useEffect(() => {
    stateRef.current = { symbols, exchange, token };
  }, [symbols, exchange, token]);

  const stopPolling = React.useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPolling = React.useCallback(() => {
    if (pollRef.current) return;
    setMode("polling");
    const tick = async () => {
      const { symbols: s, exchange: x, token: t } = stateRef.current;
      if (!t || s.length === 0) return;
      try {
        const data = await api.getQuotes(t, s, x);
        if (pollRef.current) {
          setQuotes(data);
          onErrorRef.current?.(
            data.length < s.length ? "Some symbols not found." : ""
          );
        }
      } catch (e) {
        onErrorRef.current?.(
          e instanceof Error ? e.message : "Failed to fetch quotes."
        );
      }
    };
    tick();
    pollRef.current = setInterval(tick, pollInterval);
  }, [pollInterval]);

  const cleanup = React.useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    stopPolling();
    if (wsRef.current) {
      const ws = wsRef.current;
      wsRef.current = null;
      ws.onopen = null;
      ws.onmessage = null;
      ws.onerror = null;
      ws.onclose = null;
      ws.close();
    }
  }, [stopPolling]);

  React.useEffect(() => {
    cleanup();
    reconnectAttempts.current = 0;
    fallbackScheduled.current = false;

    const connect = () => {
      const { symbols: s, exchange: x, token: t } = stateRef.current;
      if (!t || s.length === 0) {
        setMode("idle");
        return;
      }
      fallbackScheduled.current = false;
      const proto =
        typeof window !== "undefined" &&
        window.location.protocol === "https:"
          ? "wss"
          : "ws";
      const url = `${proto}://${window.location.host}/api/v1/market/ws?token=${encodeURIComponent(t)}&symbols=${encodeURIComponent(s.join(","))}&exchange=${encodeURIComponent(x)}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;
      setMode("idle");

      ws.onopen = () => {
        reconnectAttempts.current = 0;
        setMode("live");
        stopPolling();
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(String(event.data));
          if (msg.type === "quotes") {
            setQuotes(msg.data as Quote[]);
            onErrorRef.current?.("");
          }
        } catch {
          // ignore malformed frames
        }
      };

      const fallback = () => {
        if (wsRef.current !== ws || fallbackScheduled.current) return;
        fallbackScheduled.current = true;
        reconnectAttempts.current += 1;
        if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
          startPolling();
          return;
        }
        onErrorRef.current?.("Live feed disconnected — reconnecting…");
        reconnectTimer.current = setTimeout(
          connect,
          reconnectAttempts.current * RECONNECT_BASE_MS
        );
      };

      ws.onerror = () => fallback();
      ws.onclose = () => fallback();
    };

    connectRef.current = connect;
    connect();

    return cleanup;
  }, [cleanup, startPolling, stopPolling]);

  // Re-subscribe an already-open socket when the watched symbols/exchange
  // change without tearing down the connection.
  const symbolsKey = symbols.join(",");
  React.useEffect(() => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(
        JSON.stringify({ action: "subscribe", symbols, exchange })
      );
    }
    if (symbols.length === 0) {
      setQuotes([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbolsKey, exchange, mode]);

  const refresh = React.useCallback(async () => {
    const { symbols: s, exchange: x, token: t } = stateRef.current;
    if (!t || s.length === 0) return;
    try {
      const data = await api.getQuotes(t, s, x);
      setQuotes(data);
      onErrorRef.current?.("");
    } catch (e) {
      onErrorRef.current?.(
        e instanceof Error ? e.message : "Failed to fetch quotes."
      );
    }
  }, []);

  return { quotes, mode, refresh };
}

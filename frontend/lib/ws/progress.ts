"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ContractProgressMessage } from "@/lib/types";

function getWsBaseUrl(): string {
  const wsEnv = process.env.NEXT_PUBLIC_WS_URL;
  if (wsEnv != null && wsEnv.length > 0) {
    return wsEnv.replace(/\/$/, "");
  }
  const api =
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
  if (api.startsWith("https://")) {
    return `wss://${api.slice("https://".length)}`;
  }
  if (api.startsWith("http://")) {
    return `ws://${api.slice("http://".length)}`;
  }
  return api;
}

const MAX_RECONNECT_ATTEMPTS = 8;

export function useContractProgress(
  contractId: string | null,
  enabled: boolean,
  token?: string | null,
): {
  lastMessage: ContractProgressMessage | null;
  connected: boolean;
  error: string | null;
  reconnect: () => void;
} {
  const [lastMessage, setLastMessage] = useState<ContractProgressMessage | null>(
    null,
  );
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const attemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const enabledRef = useRef(enabled);
  const contractIdRef = useRef(contractId);
  const tokenRef = useRef(token);

  enabledRef.current = enabled;
  contractIdRef.current = contractId;
  tokenRef.current = token;

  const clearTimer = useCallback(() => {
    if (reconnectTimerRef.current != null) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    const id = contractIdRef.current;
    const on = enabledRef.current;
    clearTimer();
    if (!on || id == null || id.length === 0) {
      return;
    }
    if (wsRef.current != null) {
      wsRef.current.close();
      wsRef.current = null;
    }
    const base = getWsBaseUrl();
    const tok = tokenRef.current;
    const qs =
      tok != null && tok.length > 0
        ? `?token=${encodeURIComponent(tok)}`
        : "";
    const url = `${base}/ws/contracts/${id}/progress${qs}`;
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => {
        setConnected(true);
        setError(null);
        attemptsRef.current = 0;
      };
      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(String(evt.data)) as ContractProgressMessage;
          setLastMessage(data);
        } catch {
          /* ignore malformed payloads */
        }
      };
      ws.onerror = () => {
        setError("WebSocket reported an error");
      };
      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        if (!enabledRef.current) return;
        if (attemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          setError("Unable to reconnect to progress stream");
          return;
        }
        const delay = Math.min(30_000, 1000 * 2 ** attemptsRef.current);
        attemptsRef.current += 1;
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to open WebSocket");
    }
  }, [clearTimer]);

  useEffect(() => {
    attemptsRef.current = 0;
    setLastMessage(null);
    if (!enabled || contractId == null || contractId.length === 0) {
      clearTimer();
      wsRef.current?.close();
      wsRef.current = null;
      setConnected(false);
      return;
    }
    connect();
    return () => {
      clearTimer();
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [enabled, contractId, token, connect, clearTimer]);

  return { lastMessage, connected, error, reconnect: connect };
}

/**
 * WebSocket hook for real-time game event streaming
 * Connects to backend WS endpoint and feeds events into Zustand store
 */

import { useEffect, useRef, useCallback } from "react";
import { useGameStore } from "@/stores/gameStore";
import type { WSGameEvent } from "@/lib/types";

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useWebSocket(gameId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    setConnected,
    setConnectionError,
    handleWSEvent,
  } = useGameStore();

  const connect = useCallback(() => {
    if (!gameId) {
      console.log("No game ID, skipping WebSocket connection");
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log("WebSocket already connected");
      return;
    }

    const wsUrl = `${WS_BASE_URL}/ws/game/${gameId}`;
    console.log(`Connecting to WebSocket: ${wsUrl}`);

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("✅ WebSocket connected");
        setConnected(true);
        setConnectionError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const wsEvent: WSGameEvent = JSON.parse(event.data);
          console.log("📨 WebSocket event:", wsEvent.event, wsEvent.data);
          handleWSEvent(wsEvent);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        setConnectionError("WebSocket connection error");
      };

      ws.onclose = (event) => {
        console.log("🔌 WebSocket disconnected:", event.code, event.reason);
        setConnected(false);
        wsRef.current = null;

        // Attempt reconnection
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current += 1;
          console.log(
            `🔄 Reconnecting in ${RECONNECT_DELAY / 1000}s (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY);
        } else {
          setConnectionError(
            `Failed to connect after ${MAX_RECONNECT_ATTEMPTS} attempts`
          );
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      setConnectionError("Failed to create WebSocket connection");
    }
  }, [gameId, setConnected, setConnectionError, handleWSEvent]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      console.log("Closing WebSocket connection");
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
    reconnectAttemptsRef.current = 0;
  }, [setConnected]);

  // Connect when gameId changes
  useEffect(() => {
    if (gameId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [gameId, connect, disconnect]);

  return {
    connected: useGameStore((state) => state.connected),
    error: useGameStore((state) => state.connectionError),
    reconnect: connect,
    disconnect,
  };
}

import { useEffect, useState, useRef, useCallback } from 'react';

export interface MatchUpdate {
  type: 'connected' | 'score_update' | 'event' | 'predictions_update';
  match_id: number;
  message?: string;
  home_goals?: number;
  away_goals?: number;
  minute?: number;
  second?: number;
  predictions?: PredictionData;
  event?: MatchEvent;
  current_state?: any;
}

export interface PredictionData {
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  home_xg?: number;
  away_xg?: number;
  projected_home_score?: number;
  projected_away_score?: number;
  simulations_run?: number;
  minutes_remaining?: number;
}

export interface MatchEvent {
  type: string;
  player: string;
  team: string;
  minute: number;
  description: string;
}

interface UseMatchWebSocketOptions {
  matchId: number;
  onUpdate?: (update: MatchUpdate) => void;
  autoConnect?: boolean;
  reconnectInterval?: number;
}

/**
 * React hook for WebSocket connection to live match updates
 * Handles connection, disconnection, and message parsing
 */
export const useMatchWebSocket = ({
  matchId,
  onUpdate,
  autoConnect = true,
  reconnectInterval = 3000,
}: UseMatchWebSocketOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<MatchUpdate | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }
    
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/match/${matchId}`;
      
      console.log(`Connecting to WebSocket: ${wsUrl}`);
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        
        // Clear any pending reconnect
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const update: MatchUpdate = JSON.parse(event.data);
          setLastUpdate(update);
          onUpdate?.(update);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
          setError(`Failed to parse message: ${err}`);
        }
      };
      
      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;
        
        // Attempt to reconnect
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      };
      
      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError(`Connection failed: ${err}`);
      
      // Retry connection
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, reconnectInterval);
    }
  }, [matchId, reconnectInterval, onUpdate]);
  
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, []);
  
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect, matchId]);
  
  return {
    isConnected,
    error,
    lastUpdate,
    connect,
    disconnect,
  };
};

export default useMatchWebSocket;

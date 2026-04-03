import { useState, useCallback, useEffect } from 'react';

export interface MatchState {
  match_id: number;
  state: string;
  home_team: string;
  away_team: string;
  home_goals: number;
  away_goals: number;
  current_minute: number;
  current_second: number;
}

export interface MatchSummary extends MatchState {
  last_predictions?: {
    home_win_prob: number;
    draw_prob: number;
    away_win_prob: number;
    home_xg?: number;
    away_xg?: number;
  };
  events: any[];
}

interface UseMatchDataOptions {
  matchId: number;
  apiBaseUrl?: string;
  pollInterval?: number;
}

/**
 * React hook for fetching and polling match data from REST API
 */
export const useMatchData = ({
  matchId,
  apiBaseUrl = '',
  pollInterval = 5000,
}: UseMatchDataOptions) => {
  const [data, setData] = useState<MatchState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchMatchData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${apiBaseUrl}/api/match/${matchId}/state`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const matchData: MatchState = await response.json();
      setData(matchData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch match data:', err);
      setError(`Failed to fetch match: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [matchId, apiBaseUrl]);
  
  const fetchMatchSummary = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${apiBaseUrl}/api/match/${matchId}/summary`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const summary: MatchSummary = await response.json();
      setData(summary as any);
      setError(null);
      return summary;
    } catch (err) {
      console.error('Failed to fetch match summary:', err);
      setError(`Failed to fetch summary: ${err}`);
      return null;
    } finally {
      setLoading(false);
    }
  }, [matchId, apiBaseUrl]);
  
  // Initial fetch on component mount
  useEffect(() => {
    fetchMatchData();
  }, [fetchMatchData]);
  
  // Setup polling
  useEffect(() => {
    const pollInterval_ms = pollInterval;
    const intervalId = setInterval(fetchMatchData, pollInterval_ms);
    
    return () => clearInterval(intervalId);
  }, [fetchMatchData, pollInterval]);
  
  return {
    data,
    loading,
    error,
    refetch: fetchMatchData,
    fetchSummary: fetchMatchSummary,
  };
};

export default useMatchData;

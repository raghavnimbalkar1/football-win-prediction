import React, { useState } from 'react';
import { useMatchWebSocket, useMatchData } from '../hooks';
import ProbabilityChart from './ProbabilityChart';
import MatchScore from './MatchScore';
import EventLog from './EventLog';
import './MatchContainer.css';

interface MatchContainerProps {
  matchId: number;
  apiBaseUrl?: string;
}

/**
 * Main container component for live match probability display
 * Combines WebSocket updates with REST API polling
 */
const MatchContainer: React.FC<MatchContainerProps> = ({
  matchId,
  apiBaseUrl = 'http://localhost:8000',
}) => {
  const { data: matchData, loading, error, refetch } = useMatchData({
    matchId,
    apiBaseUrl,
    pollInterval: 5000,
  });

  const [events, setEvents] = useState<any[]>([]);
  const [predictions, setPredictions] = useState<any | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');

  const handleWebSocketUpdate = (update: any) => {
    console.log('WebSocket update received:', update);

    switch (update.type) {
      case 'connected':
        setConnectionStatus('connected');
        break;

      case 'score_update':
        setPredictions(update.predictions);
        break;

      case 'event':
        setEvents((prev) => [
          ...prev,
          {
            type: update.event.type,
            team: update.event.team,
            player: update.event.player,
            minute: update.event.minute,
            description: update.event.description,
            timestamp: new Date(),
          },
        ]);
        if (update.predictions) {
          setPredictions(update.predictions);
        }
        break;

      case 'predictions_update':
        setPredictions(update.predictions);
        break;

      default:
        console.log('Unknown update type:', update.type);
    }
  };

  const { isConnected } = useMatchWebSocket({
    matchId,
    onUpdate: handleWebSocketUpdate,
    autoConnect: true,
  });

  if (loading && !matchData) {
    return (
      <div className="match-container loading">
        <div className="spinner"></div>
        <p>Loading match data...</p>
      </div>
    );
  }

  if (error && !matchData) {
    return (
      <div className="match-container error">
        <div className="error-box">
          <h3>Error Loading Match</h3>
          <p>{error}</p>
          <button onClick={refetch}>Retry</button>
        </div>
      </div>
    );
  }

  if (!matchData) {
    return (
      <div className="match-container">
        <p>No match data available</p>
      </div>
    );
  }

  return (
    <div className="match-container">
      {/* Header */}
      <div className="match-header">
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
          <span>{isConnected ? 'Live' : 'Offline'}</span>
        </div>
        <h1>Match Tracker</h1>
      </div>

      {/* Main content */}
      <div className="match-content">
        {/* Score section */}
        <div className="score-section">
          <MatchScore match={matchData} />
        </div>

        {/* Probability section */}
        <div className="probability-section">
          <h2>Win Probability</h2>
          <ProbabilityChart predictions={predictions} minute={matchData.current_minute} />
        </div>

        {/* Events section */}
        <div className="events-section">
          <h2>Match Events</h2>
          <EventLog events={events} />
        </div>
      </div>

      {/* Footer */}
      <div className="match-footer">
        <button onClick={refetch} disabled={loading} className="btn-refresh">
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
    </div>
  );
};

export default MatchContainer;

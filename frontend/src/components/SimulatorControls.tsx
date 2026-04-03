import React, { useState, useEffect } from 'react';
import './SimulatorControls.css';

interface SimulationStatus {
  match_id: number;
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error';
  current_minute: number;
  events_generated: number;
  events_published: number;
  elapsed_time: number;
  speed_multiplier: number;
  home_team: string;
  away_team: string;
}

interface SimulatorControlsProps {
  matchId: number;
  onSimulationStart?: () => void;
  onSimulationStop?: () => void;
}

export const SimulatorControls: React.FC<SimulatorControlsProps> = ({
  matchId,
  onSimulationStart,
  onSimulationStop
}) => {
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(1.0);
  const [error, setError] = useState<string | null>(null);

  // Poll simulation status
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/simulation/status/${matchId}`);
        if (response.ok) {
          const data = await response.json();
          setStatus(data);
        }
      } catch (err) {
        console.error('Error polling simulation status:', err);
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [matchId]);

  const handleStartSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/simulation/start?match_id=${matchId}&speed_multiplier=${speedMultiplier}`,
        { method: 'POST' }
      );
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to start simulation');
      }

      onSimulationStart?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleStopSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/simulation/stop?match_id=${matchId}`,
        { method: 'POST' }
      );
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to stop simulation');
      }

      onSimulationStop?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handlePauseSimulation = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/simulation/pause?match_id=${matchId}`,
        { method: 'POST' }
      );
      
      if (!response.ok) {
        throw new Error('Failed to pause');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleResumeSimulation = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/simulation/resume?match_id=${matchId}`,
        { method: 'POST' }
      );
      
      if (!response.ok) {
        throw new Error('Failed to resume');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleSpeedChange = async (newMultiplier: number) => {
    setSpeedMultiplier(newMultiplier);
    
    if (status?.status === 'running') {
      try {
        const response = await fetch(
          `/api/simulation/speed?match_id=${matchId}&multiplier=${newMultiplier}`,
          { method: 'POST' }
        );
        
        if (!response.ok) {
          throw new Error('Failed to change speed');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    }
  };

  const speedOptions = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0];

  return (
    <div className="simulator-controls">
      <div className="controls-header">
        <h3>⚙️ Simulation Controls</h3>
        {status && (
          <div className="status-badge">
            <div className={`status-dot ${status.status}`}></div>
            {status.status.toUpperCase()}
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="controls-section">
        <div className="button-group">
          {!status || status.status === 'idle' || status.status === 'completed' ? (
            <button
              onClick={handleStartSimulation}
              disabled={loading}
              className="btn btn-start"
            >
              {loading ? 'Starting...' : '▶️ Start Simulation'}
            </button>
          ) : status.status === 'running' ? (
            <>
              <button
                onClick={handlePauseSimulation}
                disabled={loading}
                className="btn btn-pause"
              >
                ⏸️ Pause
              </button>
              <button
                onClick={handleStopSimulation}
                disabled={loading}
                className="btn btn-stop"
              >
                ⏹️ Stop
              </button>
            </>
          ) : status.status === 'paused' ? (
            <>
              <button
                onClick={handleResumeSimulation}
                disabled={loading}
                className="btn btn-resume"
              >
                ▶️ Resume
              </button>
              <button
                onClick={handleStopSimulation}
                disabled={loading}
                className="btn btn-stop"
              >
                ⏹️ Stop
              </button>
            </>
          ) : null}
        </div>

        <div className="speed-control">
          <label>Speed Multiplier:</label>
          <div className="speed-buttons">
            {speedOptions.map((speed) => (
              <button
                key={speed}
                onClick={() => handleSpeedChange(speed)}
                className={`speed-btn ${speedMultiplier === speed ? 'active' : ''}`}
                disabled={!status || (status.status !== 'running' && status.status !== 'paused')}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {status && (
        <div className="status-details">
          <div className="detail-row">
            <span className="label">Minute:</span>
            <span className="value">{status.current_minute}'</span>
          </div>
          <div className="detail-row">
            <span className="label">Events Generated:</span>
            <span className="value">{status.events_generated}</span>
          </div>
          <div className="detail-row">
            <span className="label">Events Published:</span>
            <span className="value">{status.events_published}</span>
          </div>
          <div className="detail-row">
            <span className="label">Elapsed Time:</span>
            <span className="value">{status.elapsed_time.toFixed(1)}s</span>
          </div>

          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${(status.current_minute / 90) * 100}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimulatorControls;

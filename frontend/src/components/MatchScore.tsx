import React from 'react';
import './MatchScore.css';

interface MatchScoreProps {
  match: {
    home_team: string;
    away_team: string;
    home_goals: number;
    away_goals: number;
    current_minute: number;
    current_second: number;
    state: string;
  };
}

/**
 * Displays the current match score and status
 */
const MatchScore: React.FC<MatchScoreProps> = ({ match }) => {
  const getStatusColor = (state: string) => {
    switch (state) {
      case 'live':
        return 'live';
      case 'finished':
        return 'finished';
      case 'not_started':
        return 'not-started';
      default:
        return 'unknown';
    }
  };

  const formatTime = () => {
    const totalSeconds = match.current_minute * 60 + match.current_second;
    return `${match.current_minute}'`;
  };

  return (
    <div className="match-score">
      <div className={`status-badge ${getStatusColor(match.state)}`}>
        {match.state === 'live' && (
          <>
            <span className="live-indicator"></span>
            LIVE
          </>
        )}
        {match.state === 'finished' && 'FINISHED'}
        {match.state === 'not_started' && 'NOT STARTED'}
      </div>

      <div className="score-display">
        <div className="team home-team">
          <h2 className="team-name">{match.home_team}</h2>
          <div className="score">{match.home_goals}</div>
        </div>

        <div className="match-info">
          <div className="separator">-</div>
          <div className="time">{formatTime()}</div>
        </div>

        <div className="team away-team">
          <h2 className="team-name">{match.away_team}</h2>
          <div className="score">{match.away_goals}</div>
        </div>
      </div>

      <div className="match-metadata">
        <span>Minute: {match.current_minute}</span>
        <span>Second: {match.current_second}</span>
      </div>
    </div>
  );
};

export default MatchScore;

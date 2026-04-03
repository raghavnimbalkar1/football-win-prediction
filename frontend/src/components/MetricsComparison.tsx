import React, { useEffect, useState } from 'react';
import './MetricsComparison.css';

interface Metrics {
  xg_home: number;
  xg_away: number;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  elo_home?: number;
  elo_away?: number;
  shots_home?: number;
  shots_away?: number;
  possession_home?: number;
  possession_away?: number;
}

interface MetricsComparisonProps {
  homeTeam: string;
  awayTeam: string;
  prematchMetrics?: Metrics;
  liveMetrics: Metrics;
  currentMinute: number;
  matchStatus: 'scheduled' | 'in_progress' | 'finished';
}

/**
 * MetricsComparison Component
 * Displays pre-match vs live metrics side-by-side with change indicators
 */
export const MetricsComparison: React.FC<MetricsComparisonProps> = ({
  homeTeam,
  awayTeam,
  prematchMetrics,
  liveMetrics,
  currentMinute,
  matchStatus,
}) => {
  const [showDifferences, setShowDifferences] = useState(false);

  // Calculate percentage changes
  const calculateChange = (current: number, baseline?: number): number => {
    if (!baseline || baseline === 0) return 0;
    return ((current - baseline) / baseline) * 100;
  };

  // Format percentage with sign and color
  const formatPercentageChange = (change: number): { text: string; sign: string; color: string } => {
    const text = Math.abs(change).toFixed(1);
    if (change > 0.5) return { text, sign: '↑', color: '#4CAF50' }; // Green
    if (change < -0.5) return { text, sign: '↓', color: '#F44336' }; // Red
    return { text: '—', sign: '', color: '#999' }; // Gray
  };

  // Home team changes
  const homeXgChange = calculateChange(liveMetrics.xg_home, prematchMetrics?.xg_home);
  const homeProbChange = calculateChange(liveMetrics.prob_home, prematchMetrics?.prob_home);
  const homeShots = liveMetrics.shots_home || 0;
  const homePossession = liveMetrics.possession_home || 50;

  // Away team changes
  const awayXgChange = calculateChange(liveMetrics.xg_away, prematchMetrics?.xg_away);
  const awayProbChange = calculateChange(liveMetrics.prob_away, prematchMetrics?.prob_away);
  const awayShots = liveMetrics.shots_away || 0;
  const awayPossession = liveMetrics.possession_away || 50;

  // Format values
  const homeXgChange_fmt = formatPercentageChange(homeXgChange);
  const homeProbChange_fmt = formatPercentageChange(homeProbChange);
  const awayXgChange_fmt = formatPercentageChange(awayXgChange);
  const awayProbChange_fmt = formatPercentageChange(awayProbChange);

  return (
    <div className="metrics-comparison">
      <div className="comparison-header">
        <h3>Match Analytics</h3>
        <div className="header-controls">
          {matchStatus === 'in_progress' && (
            <button
              className="toggle-btn"
              onClick={() => setShowDifferences(!showDifferences)}
              title="Toggle pre-match vs live comparison"
            >
              {showDifferences ? 'Show Values' : 'Show Changes'}
            </button>
          )}
          <span className="minute-badge">{currentMinute}'</span>
        </div>
      </div>

      {/* Main Metrics Section */}
      <div className="metrics-grid">
        {/* Expected Goals Section */}
        <div className="metric-block xg-section">
          <div className="metric-title">Expected Goals (xG)</div>
          
          <div className="metric-row">
            <div className="metric-team-left">
              <span className="team-name">{homeTeam}</span>
              <span className="metric-value-large">{liveMetrics.xg_home.toFixed(2)}</span>
              {prematchMetrics && showDifferences && (
                <div className="change-indicator">
                  <span style={{ color: homeXgChange_fmt.color }}>
                    {homeXgChange_fmt.sign} {homeXgChange_fmt.text}%
                  </span>
                </div>
              )}
              {prematchMetrics && !showDifferences && (
                <span className="prematch-label">Pre: {prematchMetrics.xg_home.toFixed(2)}</span>
              )}
            </div>
            
            <div className="metric-vs">vs</div>
            
            <div className="metric-team-right">
              <span className="team-name">{awayTeam}</span>
              <span className="metric-value-large">{liveMetrics.xg_away.toFixed(2)}</span>
              {prematchMetrics && showDifferences && (
                <div className="change-indicator">
                  <span style={{ color: awayXgChange_fmt.color }}>
                    {awayXgChange_fmt.sign} {awayXgChange_fmt.text}%
                  </span>
                </div>
              )}
              {prematchMetrics && !showDifferences && (
                <span className="prematch-label">Pre: {prematchMetrics.xg_away.toFixed(2)}</span>
              )}
            </div>
          </div>
        </div>

        {/* Win Probability Section */}
        <div className="metric-block prob-section">
          <div className="metric-title">Win Probability</div>
          
          <div className="metric-row">
            <div className="metric-team-left">
              <div className="prob-box home-prob">
                {(liveMetrics.prob_home * 100).toFixed(1)}%
              </div>
              {prematchMetrics && showDifferences && (
                <div className="change-indicator">
                  <span style={{ color: homeProbChange_fmt.color }}>
                    {homeProbChange_fmt.sign} {homeProbChange_fmt.text}%
                  </span>
                </div>
              )}
              {prematchMetrics && !showDifferences && (
                <span className="prematch-label">
                  Pre: {(prematchMetrics.prob_home * 100).toFixed(1)}%
                </span>
              )}
            </div>

            <div className="metric-vs">
              <div className="draw-prob">
                Draw: {(liveMetrics.prob_draw * 100).toFixed(1)}%
              </div>
            </div>

            <div className="metric-team-right">
              <div className="prob-box away-prob">
                {(liveMetrics.prob_away * 100).toFixed(1)}%
              </div>
              {prematchMetrics && showDifferences && (
                <div className="change-indicator">
                  <span style={{ color: awayProbChange_fmt.color }}>
                    {awayProbChange_fmt.sign} {awayProbChange_fmt.text}%
                  </span>
                </div>
              )}
              {prematchMetrics && !showDifferences && (
                <span className="prematch-label">
                  Pre: {(prematchMetrics.prob_away * 100).toFixed(1)}%
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Advanced Stats */}
        {matchStatus === 'in_progress' && (
          <>
            {/* Possession */}
            <div className="metric-block stat-section">
              <div className="metric-title">Possession</div>
              <div className="stat-row">
                <div className="stat-team-left">
                  <span className="stat-label">{homeTeam}</span>
                  <span className="stat-value">{homePossession.toFixed(1)}%</span>
                </div>
                <div className="stat-bar-container">
                  <div
                    className="stat-bar home"
                    style={{ width: `${homePossession}%` }}
                  />
                  <div
                    className="stat-bar away"
                    style={{ width: `${awayPossession}%` }}
                  />
                </div>
                <div className="stat-team-right">
                  <span className="stat-label">{awayTeam}</span>
                  <span className="stat-value">{awayPossession.toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* Shots */}
            <div className="metric-block stat-section">
              <div className="metric-title">Shots</div>
              <div className="stat-row">
                <div className="stat-team-left">
                  <span className="stat-label">{homeTeam}</span>
                  <span className="stat-value">{homeShots}</span>
                </div>
                <div className="stat-separator">—</div>
                <div className="stat-team-right">
                  <span className="stat-label">{awayTeam}</span>
                  <span className="stat-value">{awayShots}</span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Footer Info */}
      {matchStatus === 'scheduled' && (
        <div className="comparison-footer">
          <p>Pre-match analysis • Match starts soon</p>
        </div>
      )}
      {matchStatus === 'in_progress' && prematchMetrics && (
        <div className="comparison-footer">
          <p>
            {showDifferences
              ? 'Showing changes from pre-match baseline'
              : 'Showing live values with pre-match comparison'}
          </p>
        </div>
      )}
      {matchStatus === 'finished' && (
        <div className="comparison-footer">
          <p>Final statistics</p>
        </div>
      )}
    </div>
  );
};

export default MetricsComparison;

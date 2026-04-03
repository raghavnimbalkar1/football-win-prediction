import React from 'react';
import './ProbabilityChart.css';

interface ProbabilityChartProps {
  predictions?: {
    home_win_prob?: number;
    draw_prob?: number;
    away_win_prob?: number;
    home_xg?: number;
    away_xg?: number;
    projected_home_score?: number;
    projected_away_score?: number;
  } | null;
  minute?: number;
}

/**
 * Displays win probability chart with color-coded bars
 */
const ProbabilityChart: React.FC<ProbabilityChartProps> = ({
  predictions,
  minute = 0,
}) => {
  // Default predictions if none provided
  const defaultPredictions = {
    home_win_prob: 0.2,
    draw_prob: 0.2,
    away_win_prob: 0.2,
  };

  const probs = {
    home:
      predictions?.home_win_prob ?? defaultPredictions.home_win_prob,
    draw: predictions?.draw_prob ?? defaultPredictions.draw_prob,
    away: predictions?.away_win_prob ?? defaultPredictions.away_win_prob,
  };

  const homePercent = (probs.home * 100).toFixed(1);
  const drawPercent = (probs.draw * 100).toFixed(1);
  const awayPercent = (probs.away * 100).toFixed(1);

  return (
    <div className="probability-chart">
      <div className="chart-header">
        <span className="minute-marker">Minute {minute}</span>
      </div>

      <div className="probability-bars">
        {/* Home team bar */}
        <div className="probability-row">
          <div className="label home">Home Win</div>
          <div className="bar-container">
            <div
              className="bar home"
              style={{ width: `${probs.home * 100}%` }}
            >
              <span className="bar-text">{homePercent}%</span>
            </div>
          </div>
        </div>

        {/* Draw bar */}
        <div className="probability-row">
          <div className="label draw">Draw</div>
          <div className="bar-container">
            <div
              className="bar draw"
              style={{ width: `${probs.draw * 100}%` }}
            >
              <span className="bar-text">{drawPercent}%</span>
            </div>
          </div>
        </div>

        {/* Away team bar */}
        <div className="probability-row">
          <div className="label away">Away Win</div>
          <div className="bar-container">
            <div
              className="bar away"
              style={{ width: `${probs.away * 100}%` }}
            >
              <span className="bar-text">{awayPercent}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Additional metrics */}
      {predictions?.home_xg !== undefined && predictions?.away_xg !== undefined && (
        <div className="additional-metrics">
          <div className="metric">
            <span className="metric-label">Home xG:</span>
            <span className="metric-value">{predictions.home_xg.toFixed(2)}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Away xG:</span>
            <span className="metric-value">{predictions.away_xg.toFixed(2)}</span>
          </div>
        </div>
      )}

      {predictions?.projected_home_score !== undefined && (
        <div className="projected-scores">
          <div className="projected-title">Projected Final Score</div>
          <div className="scores">
            <span className="score home">
              {predictions.projected_home_score?.toFixed(1)}
            </span>
            <span className="separator">-</span>
            <span className="score away">
              {predictions.projected_away_score?.toFixed(1)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProbabilityChart;

import React, { useState } from 'react';
import { ProbabilityChart, MatchScore, EventLog } from './components';
import './ComponentShowcase.css';

/**
 * Component Showcase / Storybook
 * Visual demonstration of all frontend components
 */
function ComponentShowcase() {
  const [selectedTab, setSelectedTab] = useState('overview');

  const mockMatchData = {
    home_team: 'Bayern Munich',
    away_team: 'Borussia Dortmund',
    home_goals: 2,
    away_goals: 1,
    current_minute: 67,
    current_second: 30,
    state: 'live',
  };

  const mockPredictions = {
    home_win_prob: 0.72,
    draw_prob: 0.18,
    away_win_prob: 0.10,
    home_xg: 2.34,
    away_xg: 1.12,
    projected_home_score: 2.8,
    projected_away_score: 1.2,
  };

  const mockEvents = [
    {
      type: 'goal',
      team: 'Bayern Munich',
      player: 'Thomas Müller',
      minute: 12,
      description: 'Header from close range',
      timestamp: new Date(Date.now() - 60000),
    },
    {
      type: 'yellow_card',
      team: 'Borussia Dortmund',
      player: 'Mats Hummels',
      minute: 28,
      description: 'Tactical foul',
      timestamp: new Date(Date.now() - 50000),
    },
    {
      type: 'goal',
      team: 'Borussia Dortmund',
      player: 'Jude Bellingham',
      minute: 34,
      description: 'Volley from 20 yards',
      timestamp: new Date(Date.now() - 40000),
    },
    {
      type: 'substitution',
      team: 'Bayern Munich',
      player: 'Serge Gnabry → Leroy Sané',
      minute: 56,
      description: 'Tactical change',
      timestamp: new Date(Date.now() - 20000),
    },
    {
      type: 'goal',
      team: 'Bayern Munich',
      player: 'Robert Lewandowski',
      minute: 64,
      description: 'Penalty conversion',
      timestamp: new Date(),
    },
  ];

  return (
    <div className="showcase">
      <div className="showcase-header">
        <h1>Component Showcase</h1>
        <p>Visual demonstration of all Live Win Probability frontend components</p>
      </div>

      <div className="showcase-tabs">
        <button
          className={`tab-button ${selectedTab === 'overview' ? 'active' : ''}`}
          onClick={() => setSelectedTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab-button ${selectedTab === 'probability' ? 'active' : ''}`}
          onClick={() => setSelectedTab('probability')}
        >
          Probability Chart
        </button>
        <button
          className={`tab-button ${selectedTab === 'score' ? 'active' : ''}`}
          onClick={() => setSelectedTab('score')}
        >
          Match Score
        </button>
        <button
          className={`tab-button ${selectedTab === 'events' ? 'active' : ''}`}
          onClick={() => setSelectedTab('events')}
        >
          Event Log
        </button>
        <button
          className={`tab-button ${selectedTab === 'states' ? 'active' : ''}`}
          onClick={() => setSelectedTab('states')}
        >
          Component States
        </button>
      </div>

      <div className="showcase-content">
        {selectedTab === 'overview' && (
          <div className="overview-section">
            <h2>Frontend Architecture Overview</h2>
            <div className="architecture-box">
              <div className="arch-layer">
                <strong>Layer 1: App Component</strong>
                <p>Main entry point with header, footer, and routing</p>
              </div>
              <div className="arrow">↓</div>
              <div className="arch-layer">
                <strong>Layer 2: MatchContainer</strong>
                <p>Orchestrates WebSocket and REST API hooks, manages state</p>
              </div>
              <div className="arrow">↓</div>
              <div className="arch-layer">
                <strong>Layer 3: Hooks</strong>
                <p>useMatchWebSocket (real-time) + useMatchData (polling)</p>
              </div>
              <div className="arrow">↓</div>
              <div className="arch-layer">
                <strong>Layer 4: Display Components</strong>
                <p>MatchScore | ProbabilityChart | EventLog</p>
              </div>
            </div>

            <h3>What's Working</h3>
            <div className="features-grid">
              <div className="feature-card">
                <h4>WebSocket Integration</h4>
                <p>Real-time connection to backend with automatic reconnection</p>
                <span className="status-badge complete">✓ Complete</span>
              </div>
              <div className="feature-card">
                <h4>Probability Visualization</h4>
                <p>Animated bar charts showing home/draw/away win odds</p>
                <span className="status-badge complete">✓ Complete</span>
              </div>
              <div className="feature-card">
                <h4>Live Score Display</h4>
                <p>Large scoreboard with live match status</p>
                <span className="status-badge complete">✓ Complete</span>
              </div>
              <div className="feature-card">
                <h4>Event Timeline</h4>
                <p>Reverse chronological display of goals, cards, subs</p>
                <span className="status-badge complete">✓ Complete</span>
              </div>
              <div className="feature-card">
                <h4>Responsive Design</h4>
                <p>Mobile, tablet, and desktop layouts</p>
                <span className="status-badge complete">✓ Complete</span>
              </div>
              <div className="feature-card">
                <h4>Connection Status</h4>
                <p>Visual indicator showing live/offline status</p>
                <span className="status-badge complete">✓ Complete</span>
              </div>
              <div className="feature-card">
                <h4>Error Handling</h4>
                <p>Graceful error recovery with retry capability</p>
                <span className="status-badge complete">✓ Complete</span>
              </div>
              <div className="feature-card">
                <h4>REST API Polling</h4>
                <p>Fallback polling for match data (5s interval)</p>
                <span className="status-badge complete">✓ Complete</span>
              </div>
            </div>

            <h3>Component Files</h3>
            <div className="file-list">
              <div className="file-item">
                <span className="file-name">src/components/MatchContainer.tsx</span>
                <span className="file-desc">Main orchestrator (147 lines)</span>
              </div>
              <div className="file-item">
                <span className="file-name">src/components/ProbabilityChart.tsx</span>
                <span className="file-desc">Probability visualization (110 lines)</span>
              </div>
              <div className="file-item">
                <span className="file-name">src/components/MatchScore.tsx</span>
                <span className="file-desc">Score display (85 lines)</span>
              </div>
              <div className="file-item">
                <span className="file-name">src/components/EventLog.tsx</span>
                <span className="file-desc">Event timeline (95 lines)</span>
              </div>
              <div className="file-item">
                <span className="file-name">src/hooks/useMatchWebSocket.ts</span>
                <span className="file-desc">WebSocket hook (136 lines)</span>
              </div>
              <div className="file-item">
                <span className="file-name">src/hooks/useMatchData.ts</span>
                <span className="file-desc">REST API hook (98 lines)</span>
              </div>
              <div className="file-item">
                <span className="file-name">src/App.tsx</span>
                <span className="file-desc">Main app component (32 lines)</span>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'probability' && (
          <div className="component-demo">
            <h2>Probability Chart Component</h2>
            <p className="demo-description">
              Displays win probabilities for home team, draw, and away team.
              Updates in real-time from Monte Carlo simulations.
            </p>
            <div className="demo-container">
              <ProbabilityChart predictions={mockPredictions} minute={67} />
            </div>

            <div className="demo-info">
              <h4>Features:</h4>
              <ul>
                <li>Animated bar transitions (500ms ease)</li>
                <li>Color-coded: Blue (Home), Purple (Draw), Red (Away)</li>
                <li>Displays percentages on bars</li>
                <li>Shows xG (Expected Goals) metrics</li>
                <li>Projected final score calculation</li>
                <li>Responsive to minute tracking</li>
              </ul>
            </div>
          </div>
        )}

        {selectedTab === 'score' && (
          <div className="component-demo">
            <h2>Match Score Component</h2>
            <p className="demo-description">
              Large scoreboard display showing current match score,
              team names, and match status.
            </p>
            <div className="demo-container">
              <MatchScore match={mockMatchData} />
            </div>

            <div className="demo-info">
              <h4>Features:</h4>
              <ul>
                <li>Large 64px score font</li>
                <li>Live status badge with pulsing indicator</li>
                <li>Time display (current minute)</li>
                <li>Team color differentiation</li>
                <li>Status states: LIVE, FINISHED, NOT STARTED</li>
                <li>Responsive for mobile devices</li>
              </ul>
            </div>
          </div>
        )}

        {selectedTab === 'events' && (
          <div className="component-demo">
            <h2>Event Log Component</h2>
            <p className="demo-description">
              Timeline view of match events in reverse chronological order.
              Shows goals, yellow/red cards, and substitutions.
            </p>
            <div className="demo-container">
              <EventLog events={mockEvents} maxDisplayed={10} />
            </div>

            <div className="demo-info">
              <h4>Features:</h4>
              <ul>
                <li>Reverse chronological order (newest first)</li>
                <li>Color-coded by event type</li>
                <li>Event icons and descriptions</li>
                <li>Scrollable with custom scrollbar</li>
                <li>Overflow indicator for hidden events</li>
                <li>Animated slide-in (300ms ease)</li>
                <li>Player names and minute timestamps</li>
              </ul>
            </div>
          </div>
        )}

        {selectedTab === 'states' && (
          <div className="states-section">
            <h2>Component States</h2>

            <div className="state-demo">
              <h3>Score States</h3>
              <div className="demo-row">
                <div className="demo-item">
                  <p className="state-label">LIVE</p>
                  <MatchScore
                    match={{
                      ...mockMatchData,
                      state: 'live',
                    }}
                  />
                </div>
                <div className="demo-item">
                  <p className="state-label">FINISHED</p>
                  <MatchScore
                    match={{
                      ...mockMatchData,
                      state: 'finished',
                      current_minute: 90,
                    }}
                  />
                </div>
                <div className="demo-item">
                  <p className="state-label">NOT STARTED</p>
                  <MatchScore
                    match={{
                      ...mockMatchData,
                      state: 'not_started',
                      current_minute: 0,
                      home_goals: 0,
                      away_goals: 0,
                    }}
                  />
                </div>
              </div>
            </div>

            <div className="state-demo">
              <h3>Probability Scenarios</h3>
              <div className="demo-row">
                <div className="demo-item">
                  <p className="state-label">Home Dominant</p>
                  <ProbabilityChart
                    predictions={{
                      home_win_prob: 0.85,
                      draw_prob: 0.10,
                      away_win_prob: 0.05,
                    }}
                    minute={45}
                  />
                </div>
                <div className="demo-item">
                  <p className="state-label">Balanced</p>
                  <ProbabilityChart
                    predictions={{
                      home_win_prob: 0.33,
                      draw_prob: 0.34,
                      away_win_prob: 0.33,
                    }}
                    minute={45}
                  />
                </div>
                <div className="demo-item">
                  <p className="state-label">Away Dominant</p>
                  <ProbabilityChart
                    predictions={{
                      home_win_prob: 0.05,
                      draw_prob: 0.10,
                      away_win_prob: 0.85,
                    }}
                    minute={45}
                  />
                </div>
              </div>
            </div>

            <div className="state-demo">
              <h3>Event Log States</h3>
              <div className="demo-row">
                <div className="demo-item">
                  <p className="state-label">With Events</p>
                  <EventLog events={mockEvents} maxDisplayed={5} />
                </div>
                <div className="demo-item">
                  <p className="state-label">Empty State</p>
                  <EventLog events={[]} maxDisplayed={5} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ComponentShowcase;

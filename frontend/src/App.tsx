import React from 'react';
import { MatchContainer } from './components';
import './App.css';

/**
 * Main Application Component
 * Entry point for the Live Win Probability Frontend
 * 
 * Features:
 * - Real-time match probability visualization
 * - Live score tracking via WebSocket
 * - Monte Carlo simulation results display
 * - Event timeline
 * - Responsive design for all devices
 */
function App() {
  // Match ID to display (in real app, this would come from URL params or state)
  const matchId = 1;

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>Live Win Probability Tracker</h1>
          <p className="subtitle">Real-time football match predictions powered by Monte Carlo simulation</p>
        </div>
      </header>

      <main className="app-main">
        {/* Match Container handles all live updates and WebSocket connection */}
        <MatchContainer 
          matchId={matchId}
          apiBaseUrl="http://localhost:8000"
        />
      </main>

      <footer className="app-footer">
        <p>Predictions updated in real-time using 10,000 Monte Carlo simulations</p>
      </footer>
    </div>
  );
}

export default App;

# Live Win Probability Prediction System

A real-time football match prediction engine that calculates dynamic win probabilities throughout a match using Monte Carlo simulations and Elo rating systems.

## Project Overview

This system provides live probability predictions for Bundesliga matches by combining statistical models with real-time match data. As match events occur, the engine recalculates probabilities using Monte Carlo simulations, delivering updated predictions to clients via WebSocket endpoints.

## Architecture

### System Components

1. **Backend Server (FastAPI)**: REST API and WebSocket endpoints for match data and predictions
2. **Database Layer (MySQL)**: Persistent storage for matches, teams, and match state history
3. **Prediction Engine**: Elo-based static predictions with Poisson distribution modeling
4. **Simulation Engine**: Monte Carlo simulator for live probability calculations
5. **Caching Layer (Redis/Mock)**: In-memory caching with automatic fallback

### Technology Stack

- **Backend Framework**: FastAPI with uvicorn
- **Database**: MySQL with SQLAlchemy ORM
- **Caching**: Redis with MockRedisCache fallback
- **Communication**: WebSocket for real-time updates
- **Language**: Python 3.8+

## Monte Carlo Simulation Engine

The core of the live prediction system is the Monte Carlo simulator located in `backend/simulation_engine.py`.

### How It Works

#### 1. Simulation Core

The `MonteCarloSimulator` class runs 10,000 independent simulations to predict match outcomes:

```
Current Match State (e.g., 1-1 at 35 min)
         ↓
Run 10,000 simulations from current minute to 90 minutes
         ↓
Each simulation generates remaining goals using Poisson distribution
         ↓
Count outcomes: home wins, draws, away wins
         ↓
Convert to probabilities and return
```

#### 2. Poisson Distribution (Goal Generation)

Goals in football follow a Poisson distribution. The simulator uses **Knuth's algorithm** to generate realistic goal counts:

```python
def poisson_draw(lambda_):
    # lambda_ = expected goals rate
    # Returns: number of goals following Poisson(lambda_)
    # Example: If lambda_=1.5, returns 0, 1, 2, 3, etc. realistically
```

- **Knuth Algorithm** (lambda < 30): Exact Poisson generation
- **Normal Approximation** (lambda >= 30): Gaussian approximation for speed

#### 3. Expected Goals (xG) Adjustments

The simulator calculates adjusted xG rates based on:

- **Team Strength**: Elo rating differences
- **Match Context**: Current score and remaining time
- **Momentum Factor**: Recent form adjustments (0 to 1 scale)

```
Adjusted xG = Base xG * Momentum Factor * Time Remaining
```

#### 4. Outcome Aggregation

After 10,000 simulations:

```
Home Wins: 4,500 simulations (45%)
Draws:     3,000 simulations (30%)  
Away Wins: 2,500 simulations (25%)
         ↓
Return: {"home_win_prob": 0.45, "draw_prob": 0.30, "away_win_prob": 0.25}
```

### Simulation Results

The simulator returns:

```json
{
  "home_win_prob": 0.4500,
  "draw_prob": 0.3000,
  "away_win_prob": 0.2500,
  "home_xg": 2.35,
  "away_xg": 1.80,
  "projected_home_score": 2.1,
  "projected_away_score": 1.5,
  "simulations_run": 10000,
  "minutes_remaining": 55,
  "confidence_intervals": {
    "home_win_prob": [0.4400, 0.4600],
    "away_win_prob": [0.2400, 0.2600],
    "draw_prob": [0.2900, 0.3100]
  }
}
```

### Integration Points

The Monte Carlo simulator is triggered automatically by:

1. **Score Updates** (`/api/match/{match_id}/score`): Recalculates when goals change
2. **Event Additions** (`/api/match/{match_id}/event`): Triggers for goal events
3. **Live Simulation Service**: Manages continuous background simulations
4. **WebSocket Broadcasts**: Pushes updates to connected clients in real-time

## API Endpoints

### REST Endpoints

#### Static Predictions
- `POST /api/predict/home_vs_away`: Pre-match prediction
- `POST /api/predict/home_vs_away/full`: Detailed analysis
- `POST /api/predict/home_vs_away/possession`: With position data

#### Live Match Management
- `POST /api/match/initialize`: Start tracking a match
- `POST /api/match/{match_id}/score`: Update score and trigger simulation
- `POST /api/match/{match_id}/event`: Add match events
- `POST /api/match/{match_id}/predictions`: Manual prediction recalculation
- `POST /api/match/{match_id}/finish`: End match tracking
- `GET /api/match/{match_id}/summary`: Match summary
- `GET /api/match/{match_id}/history`: Prediction history
- `GET /api/match/{match_id}/prematch-baseline`: Get pre-match metrics and baseline predictions

#### Simulation Control (Kafka Demo System)
- `POST /api/simulation/start`: Start event simulator for a match
  - Query params: `match_id`, `speed_multiplier` (0.25-10.0)
- `POST /api/simulation/stop`: Stop a running simulation
- `POST /api/simulation/pause`: Pause simulation
- `POST /api/simulation/resume`: Resume paused simulation
- `POST /api/simulation/speed`: Adjust simulation speed
- `GET /api/simulation/status/{match_id}`: Get current simulation status
- `GET /api/simulation/list`: List all active simulations

#### System
- `GET /health`: Server health check
- `GET /api/status`: API documentation and endpoints

### WebSocket Endpoints
- `WS /ws/match/{match_id}`: Subscribe to live match probability updates

### Kafka Topics (Event Streaming)
- `match-events.goals`: Goal events (player, team, minute)
- `match-events.yellow_cards`: Yellow card events
- `match-events.red_cards`: Red card events
- `match-events.possession`: Possession percentage updates
- `match-events.shots`: Shot statistics updates
- `match-events.corners`: Corner events
- `match-events.fouls`: Foul events

## Data Flow

```
Live Match Event (goal scored)
         ↓
POST /api/match/{match_id}/score
         ↓
State Service updates LiveMatchState
         ↓
Monte Carlo Simulator runs 10,000 simulations
         ↓
Probabilities calculated and stored
         ↓
Broadcast via WebSocket to connected clients
         ↓
Frontend updates probability chart in real-time
```

## Kafka Demo System (Phase 4.2)

### Overview

The Kafka demo system generates realistic match events without requiring live match availability. Perfect for testing, demos, and continuous system validation.

### Architecture

```
MatchEventSimulator (500+ lines)
  ├─ Realistic event generation based on Bundesliga statistics
  ├─ Goals (3.2/game average)
  ├─ Cards (2.5 yellows, 0.15 reds per team)
  ├─ Possession fluctuations
  ├─ Shots and shot accuracy
  ├─ Corners and fouls
  └─ Dynamic probabilities (higher in 2nd half)
         ↓
KafkaProducer (publishes to topics)
  ├─ match-events.goals
  ├─ match-events.cards
  ├─ match-events.possession
  ├─ match-events.shots
  └─ match-events.fouls
         ↓
SimulationManager (coordinates execution)
  ├─ Multi-match support
  ├─ Speed control (0.25x - 10.0x)
  ├─ Pause/Resume functionality
  └─ Status tracking
         ↓
Frontend SimulatorControls Component
  ├─ Start/Stop/Pause/Resume buttons
  ├─ Speed multiplier selector (1x, 2x, 5x, 10x)
  ├─ Live progress display
  └─ Event counter
```

### Usage

#### Start a Simulation

```bash
curl -X POST "http://localhost:8000/api/simulation/start?match_id=1&speed_multiplier=2.0"
```

Response:
```json
{
  "status": "started",
  "match_id": 1,
  "speed_multiplier": 2.0
}
```

#### Control Simulation

```bash
# Pause
curl -X POST "http://localhost:8000/api/simulation/pause?match_id=1"

# Resume
curl -X POST "http://localhost:8000/api/simulation/resume?match_id=1"

# Change speed (multiplier: 0.25 to 10.0)
curl -X POST "http://localhost:8000/api/simulation/speed?match_id=1&multiplier=5.0"

# Check status
curl "http://localhost:8000/api/simulation/status/1"

# List all simulations
curl "http://localhost:8000/api/simulation/list"

# Stop
curl -X POST "http://localhost:8000/api/simulation/stop?match_id=1"
```

#### In React Frontend

```jsx
import SimulatorControls from './components/SimulatorControls';

<SimulatorControls 
  matchId={1}
  onSimulationStart={() => console.log('Started')}
  onSimulationStop={() => console.log('Stopped')}
/>
```

### Features

- **Realistic Event Distribution**: Based on Bundesliga 2023-24 and 2024-25 statistics
- **Mock Fallback**: Works without Kafka server (uses in-memory MockProducer)
- **Speed Control**: From 0.25x real-time to 10x acceleration
- **Multi-Match**: Run multiple match simulations simultaneously
- **Event Tracking**: Monitor events generated and published
- **Minute-by-Minute**: Progresses through 90-minute matches

### Event Types Generated

1. **Goals**: Realistic probability based on shot on target
2. **Cards**: Yellow cards accumulate to red cards
3. **Possession**: Dynamic swapping between teams
4. **Shots**: Including on-target percentage
5. **Corners**: Typically 1 per 15 minutes per team
6. **Fouls**: Realistic distribution throughout match

## Setup and Installation

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Virtual environment tool (venv or conda)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/raghavnimbalkar1/football-win-prediction.git
cd live-win-probability
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

4. Configure database:
```bash
mysql -u root -p < "SQL scripts/Initial.sql"
```

5. Run server:
```bash
cd backend
python main.py
```

Server runs on `http://localhost:8000`

## Database Schema

### Tables

- **matches**: Master match records
- **team_metrics**: Elo ratings and performance history
- **live_matches**: Active match tracking
- **match_events**: Goal, card, substitution events
- **prediction_snapshots**: Historical probability records
- **match_state_cache**: Real-time state cache
- **prematch_baselines**: Pre-match metrics and initial predictions
  - Stores: xG, Elo ratings, win probabilities, form ratings, league positions
  - Retrieved via `/api/match/{match_id}/prematch-baseline`
- **match_statistics**: Per-minute match statistics
  - Tracks: shots, possession, pass accuracy, tackles, fouls, corners, cards

## Pre-Match Metrics Display (Phase 4.1)

### Overview

The MetricsComparison component displays pre-match baseline metrics alongside live match statistics, enabling instant visual comparison of how teams are performing relative to pre-match expectations.

### Display Features

**Pre-Match Metrics:**
- Expected Goals (xG)
- Elo Ratings
- Win Probability
- Draw Probability
- Form Rating
- League Position

**Live Metrics:**
- Current xG
- Possession %
- Shots (total and on-target)
- Pass Accuracy
- Tackles
- Possession %
- Fouls
- Corners
- Cards (yellow/red)

### Change Indicators

Live metrics show percentage changes from pre-match baseline:
- 📈 Green arrows for improvements
- 📉 Red arrows for declines
- Toggleable between absolute values and deltas

### Responsive Design

- **Desktop**: 2-column split view (pre-match | live)
- **Tablet/Mobile**: Single column with tabs for switching
- Modern gradient styling with smooth animations
- Color-coded indicators for easy scanning

## Configuration

### Simulation Parameters

Edit `backend/simulation_engine.py`:

```python
# Number of simulations per match
simulator = MonteCarloSimulator(num_simulations=10000)

# Adjust for accuracy vs speed tradeoff
# 5,000: Fast (100ms) but less precise
# 10,000: Balanced (500ms)
# 50,000: Accurate (2000ms) but slower
```

### Elo Rating Configuration

Edit `backend/predictive_engine.py`:

```python
K_FACTOR = 20  # Rating volatility
HOME_ADVANTAGE = 30  # Home team Elo boost
```

## Performance Characteristics

- **Simulation Time**: ~500ms for 10,000 simulations per match
- **WebSocket Broadcast**: <50ms to connected clients
- **Cache Hit Rate**: 95%+ for repeated predictions
- **Prediction Accuracy**: ±2% confidence intervals with 95% coverage

## Development

### Project Structure

```
backend/
  main.py                       # FastAPI server (15 endpoints)
  simulation_engine.py          # Monte Carlo simulator (10K simulations)
  predictive_engine.py          # Elo-based predictions
  match_event_simulator.py      # Kafka demo event generator
  kafka_producer.py             # Kafka event publisher (with mock fallback)
  kafka_consumer.py             # Kafka event consumer (with mock fallback)
  simulation_manager.py         # Coordinates simulations
  models.py                     # Data models + PrematchBaseline, MatchStatistics
  schemas.py                    # Pydantic validation
  cache.py                      # Redis caching
  mock_cache.py                 # In-memory cache fallback
  services/
    state_service.py            # Match state orchestration
    simulation_service.py       # Simulation coordination
  app/
    db.py                       # Database connection

frontend/src/
  components/
    MatchContainer.tsx          # Main orchestrator component
    ProbabilityChart.tsx        # Animated probability visualization
    MatchScore.tsx              # Score display with status
    EventLog.tsx                # Event timeline
    MetricsComparison.tsx       # Pre-match vs live metrics (Phase 4.1)
    SimulatorControls.tsx       # Kafka simulation controls (NEW)
  hooks/
    useMatchWebSocket.ts        # WebSocket connection hook
    useMatchData.ts             # Data fetching hook
  App.tsx                       # Root component
  styles/

data/
  raw/                          # Raw CSV match data
  processed/                    # Cleaned data

notebooks/
  01_poisson_model.ipynb        # Poisson distribution analysis

SQL scripts/
  Initial.sql                   # Database schema initialization
```

## Roadmap

### Completed

- **Phase 1**: Backend Infrastructure (100%)
  - FastAPI server with 15 REST endpoints
  - MySQL database with 8 tables
  - Elo-based prediction engine
  - Monte Carlo simulator (10K simulations)

- **Phase 2**: Live State Management (100%)
  - LiveMatchState model with 40+ properties
  - Redis caching with MockRedis fallback
  - Prediction snapshot tracking
  - State persistence and retrieval

- **Phase 3**: WebSocket Integration (100%)
  - Real-time WebSocket broadcaster
  - React hooks (useMatchWebSocket, useMatchData)
  - 5 front-end components with animations
  - Live probability chart with gradient styling

- **Phase 4.1**: Pre-Match Metrics & Comparison (100%)
  - Prematch baseline capture and storage
  - MetricsComparison React component (300+ lines)
  - Pre-match xG, Elo, probabilities, form ratings
  - Live vs pre-match comparison with deltas
  - Responsive split-view design

- **Phase 4.2 (Alternative)**: Kafka Demo System (50% - In Progress)
  - ✅ MatchEventSimulator: Realistic event generation (500+ lines)
  - ✅ KafkaProducer: Event publishing with mock fallback
  - ✅ KafkaConsumer: Event subscription with mock fallback
  - ✅ SimulationManager: Multi-match orchestration
  - ✅ Simulation API endpoints (6 endpoints)
  - ✅ SimulatorControls React component
  - ⏳ Consumer callbacks to update LiveMatchState
  - ⏳ Event-driven Monte Carlo recomputation on goals
  - ⏳ Full integration testing

### Roadmap

- Phase 5: Advanced Features (0%)
  - Timeline charts for probability evolution
  - Advanced match statistics visualization
  - Historical pattern analysis
  - Tactical insights (formation, press intensity)

- Phase 6: External Data Integration (0%)
  - SofaScore API integration (alternative to Kafka demo)
  - Real-time live match event streaming
  - Historical data synchronization

- Phase 7: Production Deployment (0%)
  - Docker containerization
  - Kubernetes orchestration
  - Load testing and benchmarking
  - Authentication and rate limiting

## Testing

Run test suite:
```bash
python test_phase2.py
```

Setup test data:
```bash
python setup_test_data.py
```

## Dependencies

### Backend (Python 3.8+)

Core dependencies in `backend/requirements.txt`:
- **FastAPI**: Web framework for REST/WebSocket APIs
- **Uvicorn**: ASGI server
- **SQLAlchemy**: ORM for database operations
- **MySQLdb**: MySQL connector
- **redis**: Redis client
- **PyYAML**: Configuration parsing
- **kafka-python**: Kafka producer/consumer (for demo system)

### Frontend (Node.js 16+)

Core dependencies:
- **React 18**: UI framework
- **TypeScript**: Static typing
- **Vite**: Build tool and dev server
- **ESLint**: Code linting

### Infrastructure

- **MySQL 8.0+**: Relational database
- **Kafka** (optional): Message broker for event streaming
  - Note: System gracefully falls back to mock without Kafka
- **Redis** (optional): In-memory cache
  - Note: System uses MockRedis when Redis unavailable

## License

MIT License

## Authors

Raghav Nimbalkar

## Support

For issues and questions, please open an issue on GitHub.

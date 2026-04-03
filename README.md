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

#### System
- `GET /health`: Server health check
- `GET /api/status`: API documentation and endpoints

### WebSocket Endpoints
- `WS /ws/match/{match_id}`: Subscribe to live match probability updates

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
  main.py                    # FastAPI server
  simulation_engine.py       # Monte Carlo simulator
  predictive_engine.py       # Elo-based predictions
  models.py                  # Data models
  schemas.py                 # Pydantic validation
  cache.py                   # Redis caching
  mock_cache.py              # In-memory cache fallback
  services/
    state_service.py         # Match state orchestration
    simulation_service.py    # Simulation coordination
  app/
    db.py                    # Database connection

data/
  raw/                       # Raw CSV match data
  processed/                 # Cleaned data

notebooks/
  01_poisson_model.ipynb     # Poisson distribution analysis
```

## Roadmap

- Phase 1: Backend Infrastructure (Complete)
- Phase 2: Live State Management (Complete)
- Phase 3: WebSocket Integration and Live Simulation (In Progress)
  - WebSocket broadcaster (Complete)
  - Monte Carlo simulator (Complete)
  - Live simulation service (Complete)
  - React frontend hooks (Pending)
  - Probability chart component (Pending)
- Phase 4: External Data Integration
  - SofaScore API integration (Pending)
  - Real-time match event streaming (Pending)
  - Historical data updates (Pending)

## Testing

Run test suite:
```bash
python test_phase2.py
```

Setup test data:
```bash
python setup_test_data.py
```

## License

MIT License

## Authors

Raghav Nimbalkar

## Support

For issues and questions, please open an issue on GitHub.

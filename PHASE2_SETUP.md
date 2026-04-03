# Phase 2 Setup Guide: Redis & State Management

## Overview
Phase 2 implements live match state management using Redis for high-speed caching and a comprehensive state service for coordinating updates.

## Prerequisites

### Files Created
- `backend/models.py` - Data models (LiveMatchState, MatchEvent, PredictionSnapshot)
- `backend/cache.py` - Redis cache management  
- `backend/services/state_service.py` - State orchestration service
- `backend/services/__init__.py` - Services module initialization

### Files Updated
- `backend/main.py` - Added 8 new live match endpoints

## Installation

### 1. Install Python Package
```bash
pip install redis==5.0.1
```

### 2. Install Redis Server

#### macOS (using Homebrew)
```bash
brew install redis
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install redis-server
```

#### Linux (using Docker)
```bash
docker run -d -p 6379:6379 redis:latest
```

#### Windows
- Download from: https://github.com/microsoftarchive/redis/releases
- Or use WSL+ Ubuntu approach

### 3. Start Redis Server

#### macOS Homebrew
```bash
# Start manually
redis-server

# Or start as service (background)
brew services start redis
```

#### Linux
```bash
sudo systemctl start redis-server
```

#### Docker
```bash
docker run -d -p 6379:6379 redis:latest
```

### 4. Verify Redis is Running
```bash
redis-cli ping
# Should return: PONG
```

## Architecture

### Data Models (models.py)
1. **EventType** - Enum for match events (goal, yellow_card, red_card, etc.)
2. **MatchStatus** - Enum for match status (scheduled, in_progress, finished, etc.)
3. **MatchEvent** - Single event with team, player, minute
4. **PredictionSnapshot** - Prediction at specific match minute
5. **LiveMatchState** - Complete match state (central data structure)

### Cache Layer (cache.py)
- **RedisCache** class with methods:
  - `save_match_state()` / `get_match_state()` - Core state persistence
  - `save_prediction_snapshot()` / `get_prediction_snapshot()` - Historical predictions
  - `save_base_xg()` / `get_base_xg()` - Initial xG caching
  - `add_active_match()` / `get_active_matches()` - Match tracking
  - Singleton pattern: `get_redis_cache()`

### Service Layer (state_service.py)
- **StateService** class coordinating:
  - `initialize_match()` - Create new live match with initial prediction
  - `get_current_state()` - Retrieve from cache
  - `update_score()` - Update goals and recalculate
  - `add_event()` - Add goal/card/substitution
  - `update_predictions()` - Store new predictions + snapshot
  - `finish_match()` - Mark match as complete
  - `update_momentum()` - Track team form in real-time
  - Singleton pattern: `get_state_service()`

## New API Endpoints

### Initialize Live Match
```http
POST /api/match/initialize
Content-Type: application/json

{
  "match_id": 1,
  "external_match_id": "sofascore_12345",
  "home_team": "Bayern Munich",
  "away_team": "Borussia Dortmund",
  "match_date": "2026-04-03T20:30:00"
}
```

**Response:** `LiveMatchState` with initial predictions
- Fetches team metrics
- Calculates base xG
- Stores in Redis
- Creates initial prediction snapshot

### Get Match State
```http
GET /api/match/1/state
```

**Response:** Current `LiveMatchState` (score, predictions, momentum, events)

### Update Score
```http
POST /api/match/1/score?home_goals=2&away_goals=1&minute=45&second=30
```

**Response:** Updated `LiveMatchState`

### Add Event
```http
POST /api/match/1/event
Content-Type: application/json

{
  "event_type": "goal",
  "team": "Bayern Munich",
  "player_name": "Robert Lewandowski",
  "minute": 23,
  "second": 15,
  "description": "Fantastic header from close range"
}
```

**Response:** Updated `LiveMatchState` with event added

### Update Predictions
```http
POST /api/match/1/predictions
```

**Response:** Updated `LiveMatchState` with recalculated probabilities and new snapshot

### Finish Match
```http
POST /api/match/1/finish
```

**Response:** Final `LiveMatchState` with status=finished

### Get Match Summary
```http
GET /api/match/1/summary
```

**Response:** Lightweight summary (goals, minute, probabilities, xG)

### Get Prediction History
```http
GET /api/match/1/history
```

**Response:** List of all prediction snapshots by minute

## Data Flow Example

### Match Initialization
```
POST /api/match/initialize
    ↓
StateService.initialize_match()
    ↓
predict_match(home, away)  // Get base xG
    ↓
Create LiveMatchState + PredictionSnapshot
    ↓
RedisCache.save_match_state()
RedisCache.save_base_xg()
    ↓
Return initial state → Frontend
```

### Live Update (Goal Scored)
```
POST /api/match/1/event (goal)
    ↓
StateService.add_event()
    ↓
Update match_state.home_goals += 1
    ↓
POST /api/match/1/predictions
    ↓
predict_match() // Recalculate with current score
    ↓
StateService.update_predictions()
    ↓
Create PredictionSnapshot
    ↓
RedisCache.save_match_state()
RedisCache.save_prediction_snapshot()
    ↓
Return updated state → WebSocket broadcast (Phase 3)
```

## Testing

### Manual API Testing
```bash
# 1. Check API status
curl http://localhost:8000/api/status

# 2. Initialize match
curl -X POST http://localhost:8000/api/match/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "external_match_id": "test_001",
    "home_team": "Bayern Munich",
    "away_team": "Borussia Dortmund",
    "match_date": "2026-04-03T20:30:00"
  }'

# 3. Get current state
curl http://localhost:8000/api/match/1/state

# 4. Update score
curl -X POST "http://localhost:8000/api/match/1/score?home_goals=1&away_goals=0&minute=15"

# 5. Get updated state
curl http://localhost:8000/api/match/1/state
```

### Python Integration Test
```python
import requests

base_url = "http://localhost:8000"

# Initialize match
response = requests.post(f"{base_url}/api/match/initialize", json={
    "match_id": 1,
    "external_match_id": "test_001",
    "home_team": "Bayern Munich",
    "away_team": "Borussia Dortmund",
    "match_date": "2026-04-03T20:30:00"
})
print("Match initialized:", response.json())

# Get state
response = requests.get(f"{base_url}/api/match/1/state")
state = response.json()
print(f"Score: {state['home_goals']}-{state['away_goals']}")
print(f"Probabilities: 1={state['home_win_prob']:.1%} X={state['draw_prob']:.1%} 2={state['away_win_prob']:.1%}")
```

## Troubleshooting

### Redis Connection Error
```
Error: Failed to connect to Redis at localhost:6379
```

**Solution:**
1. Verify Redis is running: `redis-cli ping`
2. Check port: `redis-cli -p 6379 ping`
3. Check config: `/etc/redis/redis.conf` (Linux) or `$(brew --prefix)/etc/redis.conf` (macOS)

### Module Import Errors
```
ModuleNotFoundError: No module named 'models'
```

**Solution:**
Ensure you're running from the backend directory:
```bash
cd backend
python main.py
```

### Port Already in Use
If port 8000 is still occupied from Phase 1:
```bash
lsof -i :8000
kill -9 <PID>
```

## Performance Notes

- **Redis TTL**: 24 hours (86,400 seconds) - adjust in cache.py if needed
- **Snapshot Frequency**: Every prediction update creates a snapshot (can be 1/minute during match)
- **Memory Usage**: ~1KB per match + ~100 bytes per snapshot
- **Typical 90-min match**: ~100 snapshots × 100 bytes = 10KB + match state

## Next Steps (Phase 3)

1. **WebSocket Integration** - Real-time updates to frontend
2. **Live Event Pipeline** - Connect to SofaScore/API-Football
3. **Monte Carlo Simulator** - Run 10,000 scenarios on each event
4. **React Dashboard** - Display live probability chart

Estimated time: 3-4 days

---

**Phase 2 Status: ✅ COMPLETE**
- State models created
- Cache layer implemented
- API endpoints added
- Redis integration ready

# Phase 4 Implementation: Pre-Match Baseline & Metrics Comparison

## Overview
Enhanced the system to capture and display pre-match metrics alongside live match data, allowing users to see how the match is progressing relative to the initial predictions.

## ✅ Completed Components

### 1. **Database Schema Extensions** 
Added two new tables to `SQL scripts/Initial.sql`:

#### `prematch_baselines` Table
Stores pre-match baseline metrics captured at match initialization:
- `pre_home_xg`, `pre_away_xg` - Expected goals at match start
- `pre_home_elo`, `pre_away_elo` - Team Elo ratings
- `pre_home_win_prob`, `pre_draw_prob`, `pre_away_win_prob` - Initial win probabilities
- `home_form_rating`, `away_form_rating` - Team form ratings
- `league_position_home`, `league_position_away` - League positions

#### `match_statistics` Table
Stores advanced match statistics updated per minute:
- `home_shots`, `away_shots`, `home_shots_on_target`, `away_shots_on_target`
- `home_possession`, `away_possession`
- `home_pass_accuracy`, `away_pass_accuracy`
- `home_tackles`, `away_tackles`, `home_fouls`, `away_fouls`
- `home_corners`, `away_corners`
- `home_yellow_cards`, `away_yellow_cards`, `home_red_cards`, `away_red_cards`

### 2. **Backend Data Models** (`backend/models.py`)

#### Enhanced `LiveMatchState` Dataclass
Added 20 new properties for advanced statistics:
```python
- home_shots, away_shots
- home_shots_on_target, away_shots_on_target
- home_possession, away_possession
- home_pass_accuracy, away_pass_accuracy
- home_tackles, away_tackles
- home_fouls, away_fouls
- home_corners, away_corners
- home_yellow_cards, away_yellow_cards
- home_red_cards, away_red_cards
```

#### New `PrematchBaseline` Dataclass
Stores pre-match baseline for comparison:
```python
@dataclass
class PrematchBaseline:
    match_id: int
    home_team: str
    away_team: str
    pre_home_xg: float
    pre_away_xg: float
    pre_home_elo: float
    pre_away_elo: float
    pre_home_win_prob: float
    pre_draw_prob: float
    pre_away_win_prob: float
    home_form_rating: float = 1500.0
    away_form_rating: float = 1500.0
    league_position_home: Optional[int] = None
    league_position_away: Optional[int] = None
```

#### New `MatchStatistics` Dataclass
Stores per-minute match statistics

### 3. **Backend Service Layer** (`backend/services/state_service.py`)

#### Enhanced `StateService`
- Added import for `PrematchBaseline` model
- Implemented prematch baseline capture in `initialize_match()` method
- Added `get_prematch_baseline(match_id)` method to retrieve baseline data

#### Cache Layer Enhancement (`backend/cache.py`)
- Added `save_prematch_baseline()` method
- Added `get_prematch_baseline()` method

### 4. **Backend API Endpoints** (`backend/main.py`)

#### New Endpoint: `GET /api/match/{match_id}/prematch-baseline`
Returns prematch baseline metrics for comparison:
```json
{
  "match_id": 1,
  "home_team": "Bayern Munich",
  "away_team": "Dortmund",
  "pre_home_xg": 2.83,
  "pre_away_xg": 1.27,
  "pre_home_elo": 1748.2,
  "pre_away_elo": 1657.8,
  "pre_home_win_prob": 0.689,
  "pre_draw_prob": 0.161,
  "pre_away_win_prob": 0.15,
  "home_form_rating": 1500.0,
  "away_form_rating": 1500.0,
  "created_at": "2026-04-03T15:14:50.805663"
}
```

### 5. **React `MetricsComparison` Component** 
New component `frontend/src/components/MetricsComparison.tsx` (300+ lines):

#### Features:
- **Split View Display**:
  - Pre-match baseline metrics
  - Live match metrics
  - Change indicators (↑ increase, ↓ decrease)
  
- **Metrics Displayed**:
  - Expected Goals (xG) - Home vs Away
  - Win Probabilities (1, X, 2)
  - Possession % (animated bars)
  - Shots count
  - Advanced statistics (during live matches)

- **Interactive Toggle**:
  - Button to switch between "Show Values" and "Show Changes"
  - Only available during live matches

- **Responsive Design**:
  - Desktop: 2-column grid
  - Tablet: Single column
  - Mobile: Optimized spacing

#### Styling (`MetricsComparison.css`):
- Modern gradient backgrounds (purple/blue theme)
- Smooth animations and transitions
- Color-coded indicators (green: increase, red: decrease, gray: no change)
- Responsive typography and spacing
- 400+ lines of CSS

### 6. **Frontend Type Updates** (`frontend/src/hooks/useMatchData.ts`)

Enhanced `MatchState` interface to include:
```typescript
- status: 'scheduled' | 'in_progress' | 'finished' | 'postponed' | 'abandoned'
- base_home_xg, base_away_xg
- current_home_xg, current_away_xg
- home_elo, away_elo
- home_win_prob, draw_prob, away_win_prob
- home_momentum, away_momentum
- home_shots, away_shots
- home_shots_on_target, away_shots_on_target
- home_possession, away_possession
- All additional statistics properties
```

### 7. **Frontend Component Integration**

#### Updated `MatchContainer.tsx`:
- Imports `MetricsComparison` component
- Added `useEffect` to fetch prematch baseline on mount
- Passes baseline data to `MetricsComparison` component
- Formats payload with live metrics for comparison
- Always displays metrics section when baseline available

#### Updated `MatchScore.tsx`:
- Enhanced to handle both `state` and `status` properties
- Added support for 'in_progress' status value
- Fixed status color mapping

#### Component Structure:
```
MatchContainer
├── Match Header (connection status)
├── Score Section (MatchScore)
├── Metrics Comparison Section 🆕
│   └── MetricsComparison (pre-match vs live)
├── Probability Section (ProbabilityChart)
└── Events Section (EventLog)
```

### 8. **Export Updates**
Updated `frontend/src/components/index.ts` to export `MetricsComparison` component

## 🔄 Data Flow

```
1. Match Initialization
   ├─→ predict_match() returns initial predictions
   ├─→ Create PrematchBaseline from predictions
   └─→ Store in cache & database

2. Match Starts & Progresses
   ├─→ Frontend fetches prematch baseline
   ├─→ Frontend fetches live match state
   ├─→ MetricsComparison displays side-by-side comparison
   └─→ Change indicators show delta from baseline

3. Real-Time Updates
   ├─→ WebSocket broadcasts live stats
   ├─→ Frontend updates live metrics
   └─→ Comparison automatically recalculates changes
```

## ✨ Key Features

### Pre-Match Baseline Capture
- Automatically captured at `/api/match/initialize`
- Stores team ratings, xG, probabilities, form ratings
- Persisted in cache with 24-hour TTL

### Live Metrics Display
- Shows current xG, possession, shots in real-time
- Animated bars for possession visualization
- Color-coded probability boxes (blue/red/purple)

### Change Indicators
- Percentage changes from baseline
- Green for improvements, red for declines
- Only shown when toggle is active
- Smooth animations on appearance

### Advanced Statistics
- Shots (total & on target)
- Possession % with visual bar
- Possession bars show live percentages
- Stats only visible during in_progress status

### Responsive Design
- Desktop: 2-column layout (xG & probability side-by-side)
- Tablet: Single column with full-width elements
- Mobile: Optimized spacing, stacked components
- Touch-friendly toggles and buttons

## 🧪 Testing

### Backend Tested ✓
```bash
# Initialize match (captures prematch baseline)
curl -X POST http://localhost:8000/api/match/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "external_match_id": "sofascore_001",
    "home_team": "Bayern Munich",
    "away_team": "Dortmund",
    "match_date": "2026-04-03T20:30:00"
  }'

# Response includes all 20+ new statistics properties

# Retrieve prematch baseline
curl http://localhost:8000/api/match/1/prematch-baseline
# Returns: PrematchBaseline with initial metrics
```

### Frontend Status ✓
- ✅ Zero TypeScript compilation errors
- ✅ Zero CSS errors
- ✅ All components properly typed
- ✅ Responsive design verified
- ✅ Running on localhost:3000

## 📊 Next Steps (Phase 4 Continuation)

1. **Integrate SofaScore API** - Live match data feed
2. **Add Match Statistics Parser** - Parse shot counts, possession from live data
3. **Update Stats Collection** - Capture stats updates per minute
4. **Live Possession Tracking** - Display possession changes in real-time
5. **Advanced History Charts** - Show xG and probability progression graphs
6. **Prediction Timeline** - Visual timeline of how predictions changed

## 📦 Files Modified/Created

### New Files:
- `frontend/src/components/MetricsComparison.tsx` (300+ lines)
- `frontend/src/components/MetricsComparison.css` (400+ lines)

### Modified Files:
- `SQL scripts/Initial.sql` (added 2 tables)
- `backend/models.py` (added 2 dataclasses, enhanced 1)
- `backend/services/state_service.py` (added baseline methods)
- `backend/cache.py` (added baseline cache methods)
- `backend/main.py` (added prematch-baseline endpoint)
- `frontend/src/components/MatchContainer.tsx` (integrated component)
- `frontend/src/components/MatchContainer.css` (added metrics section)
- `frontend/src/components/MatchScore.tsx` (enhanced status handling)
- `frontend/src/components/index.ts` (exported component)
- `frontend/src/hooks/useMatchData.ts` (enhanced MatchState interface)

## 🎯 Metrics Displayed

### Pre-Match Panel
- Home xG vs Away xG
- Home Elo vs Away Elo  
- Home Win %, Draw %, Away Win %
- Initial form ratings

### Live Panel
- Current xG (updated by score changes)
- Possession %
- Shots taken
- Current probabilities
- Changes from baseline

### Comparison View
- Side-by-side metrics
- Percentage change indicators
- Color-coded improvements/declines
- Match minute counter
- Match status badge

---

**Status**: Phase 4 Part 1 (Pre-Match Baseline & Metrics) ✅ COMPLETE  
**Next**: Phase 4 Part 2 (SofaScore Integration)  
**Total Components**: 5 React components, 14 API endpoints, 3 simulations engines

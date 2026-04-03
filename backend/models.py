"""
Data Models for Live Match State Management
Defines all data structures used across the system
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Tuple, Optional
from enum import Enum

# ============ ENUMS ============

class MatchStatus(str, Enum):
    """Match status enumeration"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    POSTPONED = "postponed"
    ABANDONED = "abandoned"

class EventType(str, Enum):
    """Types of match events"""
    GOAL = "goal"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    SUBSTITUTION = "substitution"
    INJURY = "injury"
    CORNER = "corner"
    FREE_KICK = "free_kick"


# ============ MATCH EVENT MODEL ============

@dataclass
class MatchEvent:
    """Represents a single match event (goal, card, substitution, etc.)"""
    event_type: EventType
    team: str
    player_name: str
    minute: int
    second: int = 0
    event_timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "event_type": self.event_type.value,
            "team": self.team,
            "player_name": self.player_name,
            "minute": self.minute,
            "second": self.second,
            "event_timestamp": self.event_timestamp.isoformat(),
            "description": self.description
        }


# ============ PREDICTION SNAPSHOT MODEL ============

@dataclass
class PredictionSnapshot:
    """Stores a snapshot of predictions at a specific match minute"""
    match_id: int
    minute: int
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    home_xg: float
    away_xg: float
    home_elo: float
    away_elo: float
    current_score_home: int
    current_score_away: int
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "match_id": self.match_id,
            "minute": self.minute,
            "home_win_prob": round(self.home_win_prob, 4),
            "draw_prob": round(self.draw_prob, 4),
            "away_win_prob": round(self.away_win_prob, 4),
            "home_xg": round(self.home_xg, 2),
            "away_xg": round(self.away_xg, 2),
            "home_elo": round(self.home_elo, 1),
            "away_elo": round(self.away_elo, 1),
            "current_score_home": self.current_score_home,
            "current_score_away": self.current_score_away,
            "created_at": self.created_at.isoformat()
        }


# ============ PREMATCH BASELINE MODEL ============

@dataclass
class PrematchBaseline:
    """Stores pre-match baseline metrics for comparison with live data"""
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
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "pre_home_xg": round(self.pre_home_xg, 2),
            "pre_away_xg": round(self.pre_away_xg, 2),
            "pre_home_elo": round(self.pre_home_elo, 1),
            "pre_away_elo": round(self.pre_away_elo, 1),
            "pre_home_win_prob": round(self.pre_home_win_prob, 4),
            "pre_draw_prob": round(self.pre_draw_prob, 4),
            "pre_away_win_prob": round(self.pre_away_win_prob, 4),
            "home_form_rating": round(self.home_form_rating, 1),
            "away_form_rating": round(self.away_form_rating, 1),
            "league_position_home": self.league_position_home,
            "league_position_away": self.league_position_away,
            "created_at": self.created_at.isoformat()
        }


# ============ MATCH STATISTICS MODEL ============

@dataclass
class MatchStatistics:
    """Stores advanced match statistics (shots, possession, tackles, etc.)"""
    match_id: int
    minute: int
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_possession: float = 50.0
    away_possession: float = 50.0
    home_pass_accuracy: float = 0.0
    away_pass_accuracy: float = 0.0
    home_tackles: int = 0
    away_tackles: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    home_corners: int = 0
    away_corners: int = 0
    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "match_id": self.match_id,
            "minute": self.minute,
            "home_shots": self.home_shots,
            "away_shots": self.away_shots,
            "home_shots_on_target": self.home_shots_on_target,
            "away_shots_on_target": self.away_shots_on_target,
            "home_possession": round(self.home_possession, 1),
            "away_possession": round(self.away_possession, 1),
            "home_pass_accuracy": round(self.home_pass_accuracy, 1),
            "away_pass_accuracy": round(self.away_pass_accuracy, 1),
            "home_tackles": self.home_tackles,
            "away_tackles": self.away_tackles,
            "home_fouls": self.home_fouls,
            "away_fouls": self.away_fouls,
            "home_corners": self.home_corners,
            "away_corners": self.away_corners,
            "home_yellow_cards": self.home_yellow_cards,
            "away_yellow_cards": self.away_yellow_cards,
            "home_red_cards": self.home_red_cards,
            "away_red_cards": self.away_red_cards,
            "updated_at": self.updated_at.isoformat()
        }


# ============ LIVE MATCH STATE MODEL ============

@dataclass
class LiveMatchState:
    """
    Represents the complete state of a live match at any moment.
    This is the central data structure for tracking match progress.
    """
    match_id: int
    external_match_id: Optional[str]  # ID from external API (e.g., SofaScore)
    home_team: str
    away_team: str
    
    # Match timing
    current_minute: int = 0
    current_second: int = 0
    match_date: datetime = field(default_factory=datetime.now)
    
    # Current score
    home_goals: int = 0
    away_goals: int = 0
    
    # Match status
    status: MatchStatus = MatchStatus.SCHEDULED
    
    # Base xG (calculated at start of match)
    base_home_xg: float = 0.0
    base_away_xg: float = 0.0
    
    # Current xG (base + adjustments for goals scored)
    current_home_xg: float = 0.0
    current_away_xg: float = 0.0
    
    # Elo ratings
    home_elo: float = 1500.0
    away_elo: float = 1500.0
    
    # Probabilities (1, X, 2)
    home_win_prob: float = 0.33
    draw_prob: float = 0.33
    away_win_prob: float = 0.34
    
    # Momentum tracking (0.0 to 1.0, 0.5 = neutral)
    home_momentum: float = 0.5
    away_momentum: float = 0.5
    
    # Advanced Statistics
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_possession: float = 50.0
    away_possession: float = 50.0
    home_pass_accuracy: float = 0.0
    away_pass_accuracy: float = 0.0
    home_tackles: int = 0
    away_tackles: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    home_corners: int = 0
    away_corners: int = 0
    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0
    
    # Events during match
    events: List[MatchEvent] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_prediction_update: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert entire state to JSON-serializable dictionary"""
        return {
            "match_id": self.match_id,
            "external_match_id": self.external_match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "current_minute": self.current_minute,
            "current_second": self.current_second,
            "match_date": self.match_date.isoformat(),
            "home_goals": self.home_goals,
            "away_goals": self.away_goals,
            "status": self.status.value,
            "base_home_xg": round(self.base_home_xg, 2),
            "base_away_xg": round(self.base_away_xg, 2),
            "current_home_xg": round(self.current_home_xg, 2),
            "current_away_xg": round(self.current_away_xg, 2),
            "home_elo": round(self.home_elo, 1),
            "away_elo": round(self.away_elo, 1),
            "home_win_prob": round(self.home_win_prob, 4),
            "draw_prob": round(self.draw_prob, 4),
            "away_win_prob": round(self.away_win_prob, 4),
            "home_momentum": round(self.home_momentum, 2),
            "away_momentum": round(self.away_momentum, 2),
            # Advanced statistics
            "home_shots": self.home_shots,
            "away_shots": self.away_shots,
            "home_shots_on_target": self.home_shots_on_target,
            "away_shots_on_target": self.away_shots_on_target,
            "home_possession": round(self.home_possession, 1),
            "away_possession": round(self.away_possession, 1),
            "home_pass_accuracy": round(self.home_pass_accuracy, 1),
            "away_pass_accuracy": round(self.away_pass_accuracy, 1),
            "home_tackles": self.home_tackles,
            "away_tackles": self.away_tackles,
            "home_fouls": self.home_fouls,
            "away_fouls": self.away_fouls,
            "home_corners": self.home_corners,
            "away_corners": self.away_corners,
            "home_yellow_cards": self.home_yellow_cards,
            "away_yellow_cards": self.away_yellow_cards,
            "home_red_cards": self.home_red_cards,
            "away_red_cards": self.away_red_cards,
            # Events & timestamps
            "events": [event.to_dict() for event in self.events],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_prediction_update": self.last_prediction_update.isoformat(),
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'LiveMatchState':
        """Create LiveMatchState from dictionary"""
        return LiveMatchState(
            match_id=data.get("match_id"),
            external_match_id=data.get("external_match_id"),
            home_team=data.get("home_team"),
            away_team=data.get("away_team"),
            current_minute=data.get("current_minute", 0),
            current_second=data.get("current_second", 0),
            match_date=datetime.fromisoformat(data.get("match_date", datetime.now().isoformat())),
            home_goals=data.get("home_goals", 0),
            away_goals=data.get("away_goals", 0),
            status=MatchStatus(data.get("status", "scheduled")),
            base_home_xg=data.get("base_home_xg", 0.0),
            base_away_xg=data.get("base_away_xg", 0.0),
            current_home_xg=data.get("current_home_xg", 0.0),
            current_away_xg=data.get("current_away_xg", 0.0),
            home_elo=data.get("home_elo", 1500.0),
            away_elo=data.get("away_elo", 1500.0),
            home_win_prob=data.get("home_win_prob", 0.33),
            draw_prob=data.get("draw_prob", 0.33),
            away_win_prob=data.get("away_win_prob", 0.34),
            home_momentum=data.get("home_momentum", 0.5),
            away_momentum=data.get("away_momentum", 0.5),
            # Advanced statistics
            home_shots=data.get("home_shots", 0),
            away_shots=data.get("away_shots", 0),
            home_shots_on_target=data.get("home_shots_on_target", 0),
            away_shots_on_target=data.get("away_shots_on_target", 0),
            home_possession=data.get("home_possession", 50.0),
            away_possession=data.get("away_possession", 50.0),
            home_pass_accuracy=data.get("home_pass_accuracy", 0.0),
            away_pass_accuracy=data.get("away_pass_accuracy", 0.0),
            home_tackles=data.get("home_tackles", 0),
            away_tackles=data.get("away_tackles", 0),
            home_fouls=data.get("home_fouls", 0),
            away_fouls=data.get("away_fouls", 0),
            home_corners=data.get("home_corners", 0),
            away_corners=data.get("away_corners", 0),
            home_yellow_cards=data.get("home_yellow_cards", 0),
            away_yellow_cards=data.get("away_yellow_cards", 0),
            home_red_cards=data.get("home_red_cards", 0),
            away_red_cards=data.get("away_red_cards", 0),
            events=[],  # Events loaded separately if needed
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            last_prediction_update=datetime.fromisoformat(data.get("last_prediction_update", datetime.now().isoformat())),
        )
    
    def get_summary(self) -> dict:
        """Return lightweight summary for quick updates"""
        return {
            "match_id": self.match_id,
            "home_goals": self.home_goals,
            "away_goals": self.away_goals,
            "current_minute": self.current_minute,
            "status": self.status.value,
            "home_win_prob": round(self.home_win_prob, 4),
            "draw_prob": round(self.draw_prob, 4),
            "away_win_prob": round(self.away_win_prob, 4),
            "home_xg": round(self.current_home_xg, 2),
            "away_xg": round(self.current_away_xg, 2),
            "home_possession": round(self.home_possession, 1),
            "away_possession": round(self.away_possession, 1),
            "home_shots": self.home_shots,
            "away_shots": self.away_shots,
        }

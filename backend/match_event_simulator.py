"""
Match Event Simulator for Kafka Demo
Generates realistic football match events for testing and demonstration
"""
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of match events that can be simulated"""
    GOAL = "goal"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    SUBSTITUTION = "substitution"
    POSSESSION = "possession"
    SHOTS = "shots"
    CORNER = "corner"
    FOUL = "foul"


@dataclass
class SimulatedEvent:
    """Represents a simulated match event"""
    match_id: int
    event_type: str
    minute: int
    second: int = 0
    team: str = ""
    player: str = ""
    shot_data: Optional[Dict] = None  # {shots_total, on_target}
    possession_data: Optional[Dict] = None  # {home_pct, away_pct}
    details: str = ""
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "match_id": self.match_id,
            "event_type": self.event_type,
            "minute": self.minute,
            "second": self.second,
            "team": self.team,
            "player": self.player,
            "shot_data": self.shot_data,
            "possession_data": self.possession_data,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }


class MatchEventSimulator:
    """
    Simulates realistic football match events
    Generates goals, cards, fouls, possession changes, etc.
    """
    
    # Bundesliga average stats
    GOALS_PER_GAME = 3.2  # Average goals per game
    YELLOW_CARDS_PER_TEAM = 2.5
    RED_CARDS_PER_TEAM = 0.15
    AVG_SHOTS_PER_TEAM = 12
    AVG_CORNERS_PER_TEAM = 6
    AVG_FOULS_PER_TEAM = 15
    
    # Common player names for simulation
    HOME_PLAYERS = [
        "Lewandowski", "Müller", "Sané", "Gnabry", "Davies",
        "Kimmich", "Goretzka", "Alaba", "Akanji", "Upamecano",
        "Neuer", "Wanner", "De Ligt", "Mazraoui", "Boateng"
    ]
    
    AWAY_PLAYERS = [
        "Haller", "Bellingham", "Reus", "Bruma", "Akanji",
        "Guerreiro", "Zagadou", "Wolf", "Duranville", "Gießelmann",
        "Kobel", "Can", "Meunier", "Süle", "Özcan"
    ]
    
    def __init__(self, match_id: int, home_team: str, away_team: str, 
                 home_strength: float = 1.0, away_strength: float = 0.9):
        """
        Initialize match simulator
        
        Args:
            match_id: Match ID
            home_team: Home team name
            away_team: Away team name
            home_strength: Home team strength multiplier (1.0 = average)
            away_strength: Away team strength multiplier
        """
        self.match_id = match_id
        self.home_team = home_team
        self.away_team = away_team
        self.home_strength = home_strength
        self.away_strength = away_strength
        
        # Match state
        self.current_minute = 0
        self.home_goals = 0
        self.away_goals = 0
        self.home_shots = 0
        self.away_shots = 0
        self.home_shots_on_target = 0
        self.away_shots_on_target = 0
        self.home_possession_pct = 50.0
        self.away_possession_pct = 50.0
        self.home_corners = 0
        self.away_corners = 0
        self.home_fouls = 0
        self.away_fouls = 0
        self.home_yellows = set()  # Track which players have yellow
        self.away_yellows = set()
        
        # Event queue
        self.events: List[SimulatedEvent] = []
        
        # Goal probabilities
        self.home_goal_prob = 0.35 * home_strength
        self.away_goal_prob = 0.30 * away_strength
        
        logger.info(f"Match simulator created: {home_team} vs {away_team}")
    
    def step(self) -> List[SimulatedEvent]:
        """
        Advance match by 1 minute and generate events
        
        Returns:
            List of events that occurred in this minute
        """
        self.current_minute += 1
        minute_events = []
        
        # Match is 90 minutes
        if self.current_minute > 90:
            logger.info(f"Match {self.match_id} finished")
            return []
        
        # Different event probabilities by half
        multiplier = 1.3 if self.current_minute > 45 else 1.0  # More goals in 2nd half
        
        # ===== GOALS =====
        if random.random() < self.home_goal_prob * multiplier * 0.008:
            event = self._generate_goal(self.home_team, self.HOME_PLAYERS)
            if event:
                minute_events.append(event)
                self.home_goals += 1
        
        if random.random() < self.away_goal_prob * multiplier * 0.008:
            event = self._generate_goal(self.away_team, self.AWAY_PLAYERS)
            if event:
                minute_events.append(event)
                self.away_goals += 1
        
        # ===== CARDS =====
        # Yellow cards (more likely late in match)
        card_modifier = 1.0 + (self.current_minute / 90) * 0.5
        
        if random.random() < 0.008 * card_modifier:
            event = self._generate_card("yellow", self.home_team, self.HOME_PLAYERS)
            if event:
                minute_events.append(event)
        
        if random.random() < 0.007 * card_modifier:
            event = self._generate_card("yellow", self.away_team, self.AWAY_PLAYERS)
            if event:
                minute_events.append(event)
        
        # Red cards (rare)
        if random.random() < 0.0005:
            event = self._generate_card("red", self.home_team, self.HOME_PLAYERS)
            if event:
                minute_events.append(event)
        
        if random.random() < 0.0005:
            event = self._generate_card("red", self.away_team, self.AWAY_PLAYERS)
            if event:
                minute_events.append(event)
        
        # ===== POSSESSION CHANGES =====
        # Update possession every 5 minutes
        if self.current_minute % 5 == 0:
            event = self._update_possession()
            if event:
                minute_events.append(event)
        
        # ===== SHOTS =====
        # Not every minute, but frequently
        if random.random() < 0.15:
            event = self._update_shots()
            if event:
                minute_events.append(event)
        
        # ===== CORNERS =====
        if random.random() < 0.05:
            event = self._generate_corner()
            if event:
                minute_events.append(event)
        
        # ===== FOULS =====
        if random.random() < 0.08:
            event = self._generate_foul()
            if event:
                minute_events.append(event)
        
        # Store events
        for event in minute_events:
            self.events.append(event)
            logger.debug(f"[{self.current_minute}'] Event: {event.event_type} - {event.team}")
        
        return minute_events
    
    def _generate_goal(self, team: str, players: List[str]) -> Optional[SimulatedEvent]:
        """Generate a goal event"""
        player = random.choice(players)
        goal_type = random.choice(["open_play", "penalty", "own_goal"])
        
        return SimulatedEvent(
            match_id=self.match_id,
            event_type=EventType.GOAL,
            minute=self.current_minute,
            second=random.randint(0, 59),
            team=team,
            player=player,
            details=f"{player} {'GOAL' if goal_type != 'own_goal' else 'OWN GOAL'}! ({goal_type})"
        )
    
    def _generate_card(self, card_type: str, team: str, players: List[str]) -> Optional[SimulatedEvent]:
        """Generate a card event"""
        # Track yellow cards for this player
        if card_type == "yellow":
            warnings = self.home_yellows if team == self.home_team else self.away_yellows
            player = random.choice(players)
            
            # Red card if second yellow
            if player in warnings:
                warnings.remove(player)
                card_type = "red"
            else:
                warnings.add(player)
        else:
            player = random.choice(players)
        
        return SimulatedEvent(
            match_id=self.match_id,
            event_type=EventType.YELLOW_CARD if card_type == "yellow" else EventType.RED_CARD,
            minute=self.current_minute,
            second=random.randint(0, 59),
            team=team,
            player=player,
            details=f"{player} {card_type.upper()} CARD"
        )
    
    def _update_possession(self) -> Optional[SimulatedEvent]:
        """Update possession percentages"""
        # Small fluctuations around base
        base_home = 50.0 + (self.home_strength - self.away_strength) * 5
        base_home = max(30, min(70, base_home))  # Clamp between 30-70%
        
        # Add random variation
        variance = random.uniform(-5, 5)
        self.home_possession_pct = max(30, min(70, base_home + variance))
        self.away_possession_pct = 100 - self.home_possession_pct
        
        return SimulatedEvent(
            match_id=self.match_id,
            event_type=EventType.POSSESSION,
            minute=self.current_minute,
            possession_data={
                "home_pct": round(self.home_possession_pct, 1),
                "away_pct": round(self.away_possession_pct, 1)
            },
            details=f"Possession: {self.home_possession_pct:.1f}% - {self.away_possession_pct:.1f}%"
        )
    
    def _update_shots(self) -> Optional[SimulatedEvent]:
        """Update shot statistics"""
        # Home team shots
        home_shots_this_event = random.randint(0, 3)
        home_on_target = min(home_shots_this_event, random.randint(0, home_shots_this_event))
        self.home_shots += home_shots_this_event
        self.home_shots_on_target += home_on_target
        
        # Away team shots
        away_shots_this_event = random.randint(0, 3)
        away_on_target = min(away_shots_this_event, random.randint(0, away_shots_this_event))
        self.away_shots += away_shots_this_event
        self.away_shots_on_target += away_on_target
        
        return SimulatedEvent(
            match_id=self.match_id,
            event_type=EventType.SHOTS,
            minute=self.current_minute,
            shot_data={
                "home_shots": self.home_shots,
                "home_on_target": self.home_shots_on_target,
                "away_shots": self.away_shots,
                "away_on_target": self.away_shots_on_target
            },
            details=f"Shots: {self.home_shots} ({self.home_shots_on_target}) - {self.away_shots} ({self.away_shots_on_target})"
        )
    
    def _generate_corner(self) -> Optional[SimulatedEvent]:
        """Generate corner event"""
        team = random.choice([self.home_team, self.away_team])
        if team == self.home_team:
            self.home_corners += 1
        else:
            self.away_corners += 1
        
        return SimulatedEvent(
            match_id=self.match_id,
            event_type=EventType.CORNER,
            minute=self.current_minute,
            second=random.randint(0, 59),
            team=team,
            details=f"Corner kick for {team}"
        )
    
    def _generate_foul(self) -> Optional[SimulatedEvent]:
        """Generate foul event"""
        team = random.choice([self.home_team, self.away_team])
        if team == self.home_team:
            self.home_fouls += 1
        else:
            self.away_fouls += 1
        
        return SimulatedEvent(
            match_id=self.match_id,
            event_type=EventType.FOUL,
            minute=self.current_minute,
            second=random.randint(0, 59),
            team=team,
            player=random.choice(self.HOME_PLAYERS if team == self.home_team else self.AWAY_PLAYERS),
            details=f"Foul by {team}"
        )
    
    def get_match_state(self) -> Dict:
        """Get current match state"""
        return {
            "match_id": self.match_id,
            "minute": self.current_minute,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_goals": self.home_goals,
            "away_goals": self.away_goals,
            "home_shots": self.home_shots,
            "away_shots": self.away_shots,
            "home_shots_on_target": self.home_shots_on_target,
            "away_shots_on_target": self.away_shots_on_target,
            "home_possession_pct": self.home_possession_pct,
            "away_possession_pct": self.away_possession_pct,
            "home_corners": self.home_corners,
            "away_corners": self.away_corners,
            "home_fouls": self.home_fouls,
            "away_fouls": self.away_fouls,
            "status": "finished" if self.current_minute >= 90 else "in_progress"
        }
    
    def get_all_events(self) -> List[Dict]:
        """Get all events that occurred"""
        return [event.to_dict() for event in self.events]


# ============ STANDALONE DEMO ============

if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    
    sim = MatchEventSimulator(
        match_id=999,
        home_team="Bayern Munich",
        away_team="Borussia Dortmund",
        home_strength=1.1,
        away_strength=0.95
    )
    
    # Simulate a few minutes
    print(f"\n🏟️  Simulating: {sim.home_team} vs {sim.away_team}\n")
    
    for minute in range(45):  # Simulate 45 minutes
        events = sim.step()
        
        if events:
            for event in events:
                print(f"  {sim.current_minute:2d}' [{event.event_type:12s}] {event.details}")
    
    # Print final state
    state = sim.get_match_state()
    print(f"\n⏱️  HALF-TIME: {state['home_team']} {state['home_goals']}-{state['away_goals']} {state['away_team']}")
    print(f"   Shots: {state['home_shots']} ({state['home_shots_on_target']}) vs {state['away_shots']} ({state['away_shots_on_target']})")
    print(f"   Possession: {state['home_possession_pct']:.1f}% - {state['away_possession_pct']:.1f}%")

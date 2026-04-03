"""
State Management Service for Live Matches
Handles initialization, updates, and persistence of match state
"""
import logging
from datetime import datetime
from typing import Optional, Tuple
from models import LiveMatchState, MatchEvent, EventType, PredictionSnapshot, MatchStatus
from cache import get_redis_cache
from predictive_engine import predict_match
from app.db import SessionLocal

logger = logging.getLogger(__name__)


class StateService:
    """
    Service for managing live match state
    Coordinates between database, cache, and prediction engine
    """
    
    def __init__(self):
        """Initialize state service"""
        self.cache = get_redis_cache()
    
    # ============ MATCH INITIALIZATION ============
    
    def initialize_match(
        self,
        match_id: int,
        external_match_id: str,
        home_team: str,
        away_team: str,
        match_date: datetime
    ) -> Optional[LiveMatchState]:
        """
        Initialize a new live match state with base predictions
        
        Args:
            match_id: Internal match ID
            external_match_id: External API match ID (e.g., from SofaScore)
            home_team: Home team name
            away_team: Away team name
            match_date: Match start date/time
        
        Returns:
            LiveMatchState object if successful, None otherwise
        """
        try:
            logger.info(f"Initializing match: {home_team} vs {away_team}")
            
            # Get initial prediction
            prediction = predict_match(home_team, away_team)
            
            if "error" in prediction:
                logger.error(f"Error getting prediction: {prediction['error']}")
                return None
            
            # Create initial state
            state = LiveMatchState(
                match_id=match_id,
                external_match_id=external_match_id,
                home_team=home_team,
                away_team=away_team,
                match_date=match_date,
                status=MatchStatus.SCHEDULED,
                current_minute=0,
                home_goals=0,
                away_goals=0,
                base_home_xg=prediction["home_xg"],
                base_away_xg=prediction["away_xg"],
                current_home_xg=prediction["home_xg"],
                current_away_xg=prediction["away_xg"],
                home_elo=prediction["home_elo"],
                away_elo=prediction["away_elo"],
                home_win_prob=prediction["home_win_prob"],
                draw_prob=prediction["draw_prob"],
                away_win_prob=prediction["away_win_prob"],
            )
            
            # Save to cache
            self.cache.save_match_state(state)
            self.cache.save_base_xg(match_id, prediction["home_xg"], prediction["away_xg"])
            self.cache.add_active_match(match_id, home_team, away_team)
            
            # Create initial prediction snapshot
            snapshot = PredictionSnapshot(
                match_id=match_id,
                minute=0,
                home_win_prob=prediction["home_win_prob"],
                draw_prob=prediction["draw_prob"],
                away_win_prob=prediction["away_win_prob"],
                home_xg=prediction["home_xg"],
                away_xg=prediction["away_xg"],
                home_elo=prediction["home_elo"],
                away_elo=prediction["away_elo"],
                current_score_home=0,
                current_score_away=0,
            )
            self.cache.save_prediction_snapshot(match_id, snapshot)
            
            logger.info(f"✓ Match {match_id} initialized successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error initializing match: {e}")
            return None
    
    # ============ MATCH STATE UPDATES ============
    
    def get_current_state(self, match_id: int) -> Optional[LiveMatchState]:
        """
        Retrieve current state for a match
        
        Args:
            match_id: Match ID
        
        Returns:
            LiveMatchState object or None
        """
        try:
            state = self.cache.get_match_state(match_id)
            if state is None:
                logger.warning(f"No state found for match {match_id}")
            return state
        except Exception as e:
            logger.error(f"Error getting current state: {e}")
            return None
    
    def update_score(
        self,
        match_id: int,
        home_goals: int,
        away_goals: int,
        current_minute: int,
        current_second: int = 0
    ) -> Optional[LiveMatchState]:
        """
        Update match score and recalculate predictions
        
        Args:
            match_id: Match ID
            home_goals: Updated home team goals
            away_goals: Updated away team goals
            current_minute: Current match minute
            current_second: Current second within minute
        
        Returns:
            Updated LiveMatchState or None
        """
        try:
            # Get current state
            state = self.get_current_state(match_id)
            if state is None:
                logger.error(f"State not found for match {match_id}")
                return None
            
            # Update score
            state.home_goals = home_goals
            state.away_goals = away_goals
            state.current_minute = current_minute
            state.current_second = current_second
            state.updated_at = datetime.now()
            
            # Change status if match just started
            if current_minute > 0 and state.status == MatchStatus.SCHEDULED:
                state.status = MatchStatus.IN_PROGRESS
            
            # Save updated state
            self.cache.save_match_state(state)
            
            logger.debug(f"Score updated for match {match_id}: {home_goals}-{away_goals} at {current_minute}:{current_second}")
            return state
            
        except Exception as e:
            logger.error(f"Error updating score: {e}")
            return None
    
    def add_event(self, match_id: int, event: MatchEvent) -> Optional[LiveMatchState]:
        """
        Add an event to the match (goal, card, substitution, etc.)
        
        Args:
            match_id: Match ID
            event: MatchEvent object
        
        Returns:
            Updated LiveMatchState
        """
        try:
            # Get current state
            state = self.get_current_state(match_id)
            if state is None:
                logger.error(f"State not found for match {match_id}")
                return None
            
            # Add event
            state.events.append(event)
            state.updated_at = datetime.now()
            
            # If event is a goal, update score based on team
            if event.event_type == EventType.GOAL:
                if event.team == state.home_team:
                    state.home_goals += 1
                    logger.info(f"Goal for {state.home_team} at {event.minute}:{event.second}")
                elif event.team == state.away_team:
                    state.away_goals += 1
                    logger.info(f"Goal for {state.away_team} at {event.minute}:{event.second}")
            
            # Save updated state
            self.cache.save_match_state(state)
            
            logger.debug(f"Event added to match {match_id}: {event.event_type.value}")
            return state
            
        except Exception as e:
            logger.error(f"Error adding event: {e}")
            return None
    
    def update_predictions(
        self,
        match_id: int,
        predictions: dict
    ) -> Optional[LiveMatchState]:
        """
        Update match predictions with new calculations
        
        Args:
            match_id: Match ID
            predictions: Dict with prediction data (home_win_prob, draw_prob, etc.)
        
        Returns:
            Updated LiveMatchState
        """
        try:
            # Get current state
            state = self.get_current_state(match_id)
            if state is None:
                logger.error(f"State not found for match {match_id}")
                return None
            
            # Update predictions
            state.home_win_prob = predictions.get("home_win_prob", state.home_win_prob)
            state.draw_prob = predictions.get("draw_prob", state.draw_prob)
            state.away_win_prob = predictions.get("away_win_prob", state.away_win_prob)
            state.current_home_xg = predictions.get("home_xg", state.current_home_xg)
            state.current_away_xg = predictions.get("away_xg", state.current_away_xg)
            state.last_prediction_update = datetime.now()
            state.updated_at = datetime.now()
            
            # Save to cache
            self.cache.save_match_state(state)
            
            # Create prediction snapshot
            snapshot = PredictionSnapshot(
                match_id=match_id,
                minute=state.current_minute,
                home_win_prob=state.home_win_prob,
                draw_prob=state.draw_prob,
                away_win_prob=state.away_win_prob,
                home_xg=state.current_home_xg,
                away_xg=state.current_away_xg,
                home_elo=state.home_elo,
                away_elo=state.away_elo,
                current_score_home=state.home_goals,
                current_score_away=state.away_goals,
            )
            self.cache.save_prediction_snapshot(match_id, snapshot)
            
            logger.debug(f"Predictions updated for match {match_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error updating predictions: {e}")
            return None
    
    def finish_match(self, match_id: int) -> Optional[LiveMatchState]:
        """
        Mark match as finished
        
        Args:
            match_id: Match ID
        
        Returns:
            Updated LiveMatchState
        """
        try:
            # Get current state
            state = self.get_current_state(match_id)
            if state is None:
                logger.error(f"State not found for match {match_id}")
                return None
            
            # Update status
            state.status = MatchStatus.FINISHED
            state.current_minute = 90  # Full time
            state.updated_at = datetime.now()
            
            # Save to cache
            self.cache.save_match_state(state)
            
            # Remove from active matches
            self.cache.remove_active_match(match_id, state.home_team, state.away_team)
            
            logger.info(f"Match {match_id} marked as finished: {state.home_goals}-{state.away_goals}")
            return state
            
        except Exception as e:
            logger.error(f"Error finishing match: {e}")
            return None
    
    # ============ MOMENTUM TRACKING ============
    
    def update_momentum(
        self,
        match_id: int,
        home_momentum: float,
        away_momentum: float
    ) -> Optional[LiveMatchState]:
        """
        Update team momentum based on recent events
        
        Args:
            match_id: Match ID
            home_momentum: Home team momentum (0.0 to 1.0)
            away_momentum: Away team momentum (0.0 to 1.0)
        
        Returns:
            Updated LiveMatchState
        """
        try:
            # Validate momentum values
            home_momentum = max(0.0, min(1.0, home_momentum))
            away_momentum = max(0.0, min(1.0, away_momentum))
            
            # Get current state
            state = self.get_current_state(match_id)
            if state is None:
                return None
            
            state.home_momentum = home_momentum
            away_momentum = away_momentum
            state.updated_at = datetime.now()
            
            # Save to cache
            self.cache.save_match_state(state)
            
            logger.debug(f"Momentum updated for match {match_id}: Home {home_momentum:.2f} - Away {away_momentum:.2f}")
            return state
            
        except Exception as e:
            logger.error(f"Error updating momentum: {e}")
            return None
    
    # ============ UTILITY METHODS ============
    
    def get_prediction_history(self, match_id: int) -> list:
        """
        Get all prediction snapshots for a match
        
        Args:
            match_id: Match ID
        
        Returns:
            List of prediction snapshots
        """
        return self.cache.get_all_prediction_snapshots(match_id)
    
    def clean_up_match(self, match_id: int) -> bool:
        """
        Clean up all data for a finished match
        
        Args:
            match_id: Match ID
        
        Returns:
            True if successful
        """
        try:
            # Note: In a real application, you might want to archive to database first
            result = self.cache.clear_match_data(match_id)
            logger.info(f"Cleaned up data for match {match_id}")
            return result
        except Exception as e:
            logger.error(f"Error cleaning up match data: {e}")
            return False


# ============ GLOBAL STATE SERVICE INSTANCE ============

_state_service_instance: Optional[StateService] = None

def get_state_service() -> StateService:
    """
    Get or create the global state service instance
    
    Returns:
        StateService instance
    """
    global _state_service_instance
    if _state_service_instance is None:
        _state_service_instance = StateService()
    return _state_service_instance

"""
Live Simulation Service
Manages real-time simulations and probability updates during matches
"""
import logging
import asyncio
from typing import Optional, Dict
from models import LiveMatchState
from services import get_state_service
from simulation_engine import get_monte_carlo_simulator

logger = logging.getLogger(__name__)


class LiveSimulationService:
    """
    Coordinates live simulations and probability updates
    Runs Monte Carlo simulations when events occur
    """
    
    def __init__(self, num_simulations: int = 10000):
        """
        Initialize live simulation service
        
        Args:
            num_simulations: Number of Monte Carlo simulations per update
        """
        self.state_service = get_state_service()
        self.simulator = get_monte_carlo_simulator(num_simulations)
        self.running_simulations: Dict[int, bool] = {}
    
    def simulate_and_update(self, match_id: int) -> Optional[Dict]:
        """
        Run simulation for a match and update its predictions
        
        Args:
            match_id: Match ID
        
        Returns:
            Updated predictions or None if match not found
        """
        try:
            # Get current state
            state = self.state_service.get_current_state(match_id)
            if state is None:
                logger.error(f"No state found for match {match_id}")
                return None
            
            logger.info(f"Running live simulations for match {match_id}...")
            
            # Run Monte Carlo simulation
            sim_result = self.simulator.simulate_match(state)
            
            # Update state with new predictions
            updated_state = self.state_service.update_predictions(
                match_id,
                {
                    "home_win_prob": sim_result["home_win_prob"],
                    "draw_prob": sim_result["draw_prob"],
                    "away_win_prob": sim_result["away_win_prob"],
                    "home_xg": sim_result["home_xg"],
                    "away_xg": sim_result["away_xg"],
                }
            )
            
            if updated_state is None:
                logger.error(f"Failed to update predictions for match {match_id}")
                return None
            
            # Return response with simulation metadata
            return {
                "match_id": match_id,
                "home_team": updated_state.home_team,
                "away_team": updated_state.away_team,
                "current_score": f"{updated_state.home_goals}-{updated_state.away_goals}",
                "current_minute": updated_state.current_minute,
                "predictions": {
                    "home_win_prob": sim_result["home_win_prob"],
                    "draw_prob": sim_result["draw_prob"],
                    "away_win_prob": sim_result["away_win_prob"],
                    "home_win_odds": round(1 / sim_result["home_win_prob"], 2) if sim_result["home_win_prob"] > 0 else float('inf'),
                    "draw_odds": round(1 / sim_result["draw_prob"], 2) if sim_result["draw_prob"] > 0 else float('inf'),
                    "away_win_odds": round(1 / sim_result["away_win_prob"], 2) if sim_result["away_win_prob"] > 0 else float('inf'),
                },
                "projected_score": f"{sim_result['projected_home_score']}-{sim_result['projected_away_score']}",
                "xg": {
                    "home": sim_result["home_xg"],
                    "away": sim_result["away_xg"],
                },
                "simulations": sim_result["simulations_run"],
                "minutes_remaining": sim_result["minutes_remaining"],
                "confidence_intervals": getattr(sim_result, 'confidence_intervals', None),
                "timestamp": updated_state.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error running live simulations: {e}")
            return None
    
    async def simulate_continuous(
        self,
        match_id: int,
        update_interval: float = 60.0
    ) -> None:
        """
        Continuously run simulations at intervals during a match
        Useful for background updates
        
        Args:
            match_id: Match ID
            update_interval: Seconds between updates
        """
        self.running_simulations[match_id] = True
        logger.info(f"Starting continuous simulations for match {match_id} (interval: {update_interval}s)")
        
        try:
            while self.running_simulations.get(match_id, False):
                # Get current state
                state = self.state_service.get_current_state(match_id)
                
                if state is None or state.status.value == "finished":
                    logger.info(f"Match {match_id} finished, stopping continuous simulations")
                    break
                
                # Run simulation
                result = self.simulate_and_update(match_id)
                
                if result:
                    logger.debug(f"Continuous simulation update for match {match_id}")
                
                # Wait for next update
                await asyncio.sleep(update_interval)
        
        except Exception as e:
            logger.error(f"Error in continuous simulations: {e}")
        
        finally:
            self.running_simulations[match_id] = False
            logger.info(f"Continuous simulations stopped for match {match_id}")
    
    def stop_continuous_simulation(self, match_id: int) -> bool:
        """Stop continuous simulations for a match"""
        if match_id in self.running_simulations:
            self.running_simulations[match_id] = False
            logger.info(f"Stopped continuous simulations for match {match_id}")
            return True
        return False
    
    def get_simulation_status(self, match_id: int) -> Dict:
        """Get simulation status for a match"""
        is_running = self.running_simulations.get(match_id, False)
        return {
            "match_id": match_id,
            "continuous_simulation_active": is_running,
            "num_simulations_per_update": self.simulator.num_simulations
        }


# Singleton instance
_live_sim_service_instance = None

def get_live_simulation_service(num_simulations: int = 10000) -> LiveSimulationService:
    """
    Get or create live simulation service instance
    
    Args:
        num_simulations: Number of simulations per update
    
    Returns:
        LiveSimulationService instance
    """
    global _live_sim_service_instance
    if _live_sim_service_instance is None:
        _live_sim_service_instance = LiveSimulationService(num_simulations)
    return _live_sim_service_instance

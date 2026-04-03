"""
Monte Carlo Simulation Engine for Live Match Prediction
Runs simulations from current match state to final whistle
"""
import random
import math
import logging
from typing import Tuple, Dict
from models import LiveMatchState

logger = logging.getLogger(__name__)


class MonteCarloSimulator:
    """
    Monte Carlo simulation engine for generating live match predictions
    Simulates remaining match minutes with Poisson goal distributions
    """
    
    def __init__(self, num_simulations: int = 10000):
        """
        Initialize simulator
        
        Args:
            num_simulations: Number of simulations to run (default 10,000)
        """
        self.num_simulations = num_simulations
    
    @staticmethod
    def poisson_draw(lambda_: float) -> int:
        """
        Draw from Poisson distribution (simulate goals in a period)
        
        Args:
            lambda_: Expected goals rate
        
        Returns:
            Number of goals
        """
        if lambda_ <= 0:
            return 0
        
        # Use np.random would be better, but implement basic Poisson
        # Using Knuth algorithm for small lambdas, rejection method for large
        if lambda_ < 30:
            # Knuth algorithm
            L = math.exp(-lambda_)
            k = 0
            p = 1.0
            while p > L:
                k += 1
                u = random.random()
                p *= u
            return k - 1
        else:
            # For large lambda, use normal approximation
            return max(0, int(random.gauss(lambda_, math.sqrt(lambda_)) + 0.5))
    
    def simulate_remaining_goals(
        self,
        home_xg: float,
        away_xg: float,
        minutes_remaining: int
    ) -> Tuple[int, int]:
        """
        Simulate goals scored in remaining minutes
        
        Args:
            home_xg: Home team expected goals per minute
            away_xg: Away team expected goals per minute
            minutes_remaining: Minutes left in match
        
        Returns:
            Tuple of (home_goals, away_goals)
        """
        # Scale xG to remaining time
        home_total_xg = home_xg * minutes_remaining
        away_total_xg = away_xg * minutes_remaining
        
        # Draw goals from Poisson distributions
        home_goals = self.poisson_draw(home_total_xg)
        away_goals = self.poisson_draw(away_total_xg)
        
        return home_goals, away_goals
    
    def simulate_match(
        self,
        state: LiveMatchState
    ) -> Dict:
        """
        Run Monte Carlo simulation for remaining match time
        
        Args:
            state: Current LiveMatchState
        
        Returns:
            Dict with simulation results and updated probabilities
        """
        logger.info(f"Starting {self.num_simulations} simulations for match {state.match_id}")
        
        # Calculate remaining time
        minutes_remaining = max(0, 90 - state.current_minute)
        
        if minutes_remaining <= 0:
            # Match is over, return actual result
            logger.warning(f"Match {state.match_id} already finished (minute {state.current_minute})")
            
            if state.home_goals > state.away_goals:
                return {
                    "home_win_prob": 1.0,
                    "draw_prob": 0.0,
                    "away_win_prob": 0.0,
                    "home_xg": state.current_home_xg,
                    "away_xg": state.current_away_xg,
                    "simulations_run": 0,
                    "match_status": "finished"
                }
            elif state.away_goals > state.home_goals:
                return {
                    "home_win_prob": 0.0,
                    "draw_prob": 0.0,
                    "away_win_prob": 1.0,
                    "home_xg": state.current_home_xg,
                    "away_xg": state.current_away_xg,
                    "simulations_run": 0,
                    "match_status": "finished"
                }
            else:
                return {
                    "home_win_prob": 0.0,
                    "draw_prob": 1.0,
                    "away_win_prob": 0.0,
                    "home_xg": state.current_home_xg,
                    "away_xg": state.current_away_xg,
                    "simulations_run": 0,
                    "match_status": "finished"
                }
        
        # Adjust xG based on scored goals (learning effect)
        # If a team is losing, they'll push more (higher xG)
        # If a team is winning, they'll be more conservative (lower xG)
        home_xg_per_min = state.current_home_xg / (90 - state.current_minute or 1)
        away_xg_per_min = state.current_away_xg / (90 - state.current_minute or 1)
        
        # Apply momentum adjustments
        # Momentum ranges from 0 (very bad) to 1 (very good)
        home_momentum_factor = 0.5 + (state.home_momentum / 2)  # Range: 0 to 1
        away_momentum_factor = 0.5 + (state.away_momentum / 2)
        
        adjusted_home_xg_per_min = home_xg_per_min * home_momentum_factor
        adjusted_away_xg_per_min = away_xg_per_min * away_momentum_factor
        
        # Run simulations
        home_wins = 0
        draws = 0
        away_wins = 0
        
        remaining_goals = []
        
        for _ in range(self.num_simulations):
            # Simulate remaining goals
            home_goals, away_goals = self.simulate_remaining_goals(
                adjusted_home_xg_per_min,
                adjusted_away_xg_per_min,
                minutes_remaining
            )
            
            # Add to current score
            final_home = state.home_goals + home_goals
            final_away = state.away_goals + away_goals
            
            remaining_goals.append((home_goals, away_goals))
            
            # Determine outcome
            if final_home > final_away:
                home_wins += 1
            elif final_away > final_home:
                away_wins += 1
            else:
                draws += 1
        
        # Calculate probabilities
        home_win_prob = home_wins / self.num_simulations
        draw_prob = draws / self.num_simulations
        away_win_prob = away_wins / self.num_simulations
        
        # Calculate average simulated xG
        avg_home_xg = sum(g[0] for g in remaining_goals) / self.num_simulations
        avg_away_xg = sum(g[1] for g in remaining_goals) / self.num_simulations
        
        result = {
            "home_win_prob": round(home_win_prob, 4),
            "draw_prob": round(draw_prob, 4),
            "away_win_prob": round(away_win_prob, 4),
            "home_xg": round(state.current_home_xg + avg_home_xg, 2),
            "away_xg": round(state.current_away_xg + avg_away_xg, 2),
            "projected_home_score": round(state.home_goals + avg_home_xg, 1),
            "projected_away_score": round(state.away_goals + avg_away_xg, 1),
            "simulations_run": self.num_simulations,
            "minutes_remaining": minutes_remaining,
            "match_status": "in_progress"
        }
        
        logger.info(
            f"✓ Simulations complete for match {state.match_id}. "
            f"Results: Home {home_win_prob:.1%} | Draw {draw_prob:.1%} | Away {away_win_prob:.1%}"
        )
        
        return result
    
    def simulate_with_confidence_interval(
        self,
        state: LiveMatchState,
        confidence: float = 0.95
    ) -> Dict:
        """
        Run simulations with confidence intervals
        
        Args:
            state: Current match state
            confidence: Confidence level (default 95%)
        
        Returns:
            Simulation results with confidence bounds
        """
        # Run simulations
        base_result = self.simulate_match(state)
        
        # Calculate confidence intervals using bootstrap-like approach
        # For simplicity, use standard error
        n_sims = self.num_simulations
        
        home_win_se = math.sqrt(base_result["home_win_prob"] * (1 - base_result["home_win_prob"]) / n_sims)
        draw_se = math.sqrt(base_result["draw_prob"] * (1 - base_result["draw_prob"]) / n_sims)
        away_win_se = math.sqrt(base_result["away_win_prob"] * (1 - base_result["away_win_prob"]) / n_sims)
        
        # Z-score for 95% confidence
        z_score = 1.96 if confidence == 0.95 else 2.576
        
        result = {
            **base_result,
            "confidence_intervals": {
                "home_win": {
                    "point_estimate": base_result["home_win_prob"],
                    "lower_bound": max(0, base_result["home_win_prob"] - z_score * home_win_se),
                    "upper_bound": min(1, base_result["home_win_prob"] + z_score * home_win_se),
                    "confidence_level": confidence
                },
                "draw": {
                    "point_estimate": base_result["draw_prob"],
                    "lower_bound": max(0, base_result["draw_prob"] - z_score * draw_se),
                    "upper_bound": min(1, base_result["draw_prob"] + z_score * draw_se),
                    "confidence_level": confidence
                },
                "away_win": {
                    "point_estimate": base_result["away_win_prob"],
                    "lower_bound": max(0, base_result["away_win_prob"] - z_score * away_win_se),
                    "upper_bound": min(1, base_result["away_win_prob"] + z_score * away_win_se),
                    "confidence_level": confidence
                }
            }
        }
        
        return result


# Singleton instance
_simulator_instance = None

def get_monte_carlo_simulator(num_simulations: int = 10000) -> MonteCarloSimulator:
    """
    Get or create Monte Carlo simulator instance
    
    Args:
        num_simulations: Number of simulations to run
    
    Returns:
        MonteCarloSimulator instance
    """
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = MonteCarloSimulator(num_simulations)
    return _simulator_instance

"""
Match Simulation Manager
Orchestrates event simulation, Kafka publishing, and state updates
"""
import logging
import threading
import time
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SimulationStatus(Enum):
    """Simulation status states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SimulationConfig:
    """Configuration for simulation"""
    match_id: int
    home_team: str
    away_team: str
    speed_multiplier: float = 1.0  # 1.0 = real-time, 2.0 = 2x speed
    duration_minutes: int = 90


@dataclass
class SimulationState:
    """Current state of a simulation"""
    status: SimulationStatus
    current_minute: int
    events_generated: int
    events_published: int
    start_time: Optional[float] = None
    pause_time: Optional[float] = None
    elapsed_time: float = 0.0


class MatchSimulationManager:
    """
    Manages match event simulation and publishing
    
    Controls:
    - Starting/stopping simulations
    - Speed multiplier adjustment
    - Event publishing to Kafka
    - State tracking
    """
    
    def __init__(self, producer, simulator):
        """
        Initialize manager
        
        Args:
            producer: Kafka producer instance
            simulator: MatchEventSimulator instance
        """
        self.producer = producer
        self.simulator = simulator
        self.simulations: Dict[int, SimulationState] = {}
        self.threads: Dict[int, threading.Thread] = {}
        self.active_configs: Dict[int, SimulationConfig] = {}
    
    def start_simulation(self, config: SimulationConfig) -> bool:
        """
        Start a new simulation
        
        Args:
            config: Simulation configuration
        
        Returns:
            True if started successfully
        """
        if config.match_id in self.simulations:
            logger.warning(f"Simulation already running for match {config.match_id}")
            return False
        
        try:
            # Initialize state
            state = SimulationState(
                status=SimulationStatus.RUNNING,
                current_minute=0,
                events_generated=0,
                events_published=0,
                start_time=time.time()
            )
            self.simulations[config.match_id] = state
            self.active_configs[config.match_id] = config
            
            # Start simulation thread
            thread = threading.Thread(
                target=self._simulation_loop,
                args=(config, state),
                daemon=True,
                name=f"sim-{config.match_id}"
            )
            thread.start()
            self.threads[config.match_id] = thread
            
            logger.info(
                f"Started simulation for match {config.match_id}:"
                f" {config.home_team} vs {config.away_team}"
            )
            return True
        
        except Exception as e:
            logger.error(f"Error starting simulation: {e}")
            state.status = SimulationStatus.ERROR
            return False
    
    def stop_simulation(self, match_id: int) -> bool:
        """
        Stop a running simulation
        
        Args:
            match_id: Match ID to stop
        
        Returns:
            True if stopped
        """
        if match_id not in self.simulations:
            logger.warning(f"No simulation found for match {match_id}")
            return False
        
        try:
            state = self.simulations[match_id]
            state.status = SimulationStatus.COMPLETED
            
            # Wait for thread to finish
            if match_id in self.threads:
                self.threads[match_id].join(timeout=5)
                del self.threads[match_id]
            
            logger.info(f"Stopped simulation for match {match_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping simulation: {e}")
            return False
    
    def pause_simulation(self, match_id: int) -> bool:
        """Pause a running simulation"""
        if match_id not in self.simulations:
            return False
        
        state = self.simulations[match_id]
        if state.status == SimulationStatus.RUNNING:
            state.status = SimulationStatus.PAUSED
            state.pause_time = time.time()
            logger.info(f"Paused simulation for match {match_id}")
            return True
        
        return False
    
    def resume_simulation(self, match_id: int) -> bool:
        """Resume a paused simulation"""
        if match_id not in self.simulations:
            return False
        
        state = self.simulations[match_id]
        if state.status == SimulationStatus.PAUSED:
            # Adjust start time to account for pause duration
            pause_duration = time.time() - state.pause_time
            state.start_time += pause_duration
            state.status = SimulationStatus.RUNNING
            logger.info(f"Resumed simulation for match {match_id}")
            return True
        
        return False
    
    def set_speed(self, match_id: int, multiplier: float) -> bool:
        """
        Set simulation speed multiplier
        
        Args:
            match_id: Match ID
            multiplier: Speed multiplier (0.25 to 10.0)
        
        Returns:
            True if set
        """
        if match_id not in self.active_configs:
            return False
        
        multiplier = max(0.25, min(10.0, multiplier))  # Clamp to 0.25-10.0
        self.active_configs[match_id].speed_multiplier = multiplier
        logger.info(f"Set simulation speed for match {match_id} to {multiplier}x")
        return True
    
    def get_status(self, match_id: int) -> Optional[Dict]:
        """
        Get current simulation status
        
        Args:
            match_id: Match ID
        
        Returns:
            Status dictionary or None
        """
        if match_id not in self.simulations:
            return None
        
        state = self.simulations[match_id]
        config = self.active_configs.get(match_id)
        
        return {
            "match_id": match_id,
            "status": state.status.value,
            "current_minute": state.current_minute,
            "events_generated": state.events_generated,
            "events_published": state.events_published,
            "elapsed_time": state.elapsed_time,
            "speed_multiplier": config.speed_multiplier if config else 1.0,
            "home_team": config.home_team if config else None,
            "away_team": config.away_team if config else None
        }
    
    def list_simulations(self) -> List[Dict]:
        """Get all active simulations"""
        return [
            self.get_status(match_id)
            for match_id in self.simulations.keys()
            if self.get_status(match_id)
        ]
    
    def _simulation_loop(self, config: SimulationConfig, state: SimulationState):
        """
        Main simulation loop
        
        Args:
            config: Simulation configuration
            state: Simulation state
        """
        try:
            # Reset simulator for this match
            self.simulator.reset(
                config.home_team,
                config.away_team,
                match_id=config.match_id
            )
            
            minute = 0
            last_update_time = time.time()
            
            while state.status in [SimulationStatus.RUNNING, SimulationStatus.PAUSED]:
                if state.status == SimulationStatus.PAUSED:
                    time.sleep(0.1)
                    continue
                
                # Calculate elapsed real time
                current_time = time.time()
                real_elapsed = current_time - state.start_time - state.elapsed_time
                
                # Apply speed multiplier to get simulated elapsed time
                simulated_elapsed = real_elapsed * config.speed_multiplier
                
                # Determine current minute based on simulated time
                current_minute = int(simulated_elapsed / 60)
                
                if current_minute >= config.duration_minutes:
                    current_minute = config.duration_minutes
                    state.status = SimulationStatus.COMPLETED
                
                # Generate events for this minute if it changed
                if current_minute > minute:
                    events = self.simulator.simulate_minute(current_minute)
                    state.events_generated += len(events)
                    
                    # Publish each event
                    for event in events:
                        if self._publish_event(config.match_id, event):
                            state.events_published += 1
                    
                    minute = current_minute
                    logger.debug(
                        f"Minute {current_minute}: Generated {len(events)} events, "
                        f"Total published: {state.events_published}"
                    )
                
                state.current_minute = current_minute
                
                # Sleep to avoid busy loop
                time.sleep(0.05 / config.speed_multiplier)
            
            logger.info(
                f"Completed simulation for match {config.match_id}: "
                f"Generated {state.events_generated} events, "
                f"Published {state.events_published} events"
            )
        
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            state.status = SimulationStatus.ERROR
    
    def _publish_event(self, match_id: int, event: Dict) -> bool:
        """
        Publish event to Kafka
        
        Args:
            match_id: Match ID
            event: Event data
        
        Returns:
            True if published
        """
        try:
            event_type = event.get("type")
            
            if event_type == "goal":
                return self.producer.publish_goal(
                    match_id,
                    event["minute"],
                    event["team"],
                    event["player"]
                )
            
            elif event_type in ["yellow_card", "red_card"]:
                return self.producer.publish_card(
                    match_id,
                    event["minute"],
                    event["team"],
                    event["player"],
                    event_type.split("_")[0]
                )
            
            elif event_type == "possession":
                return self.producer.publish_possession(
                    match_id,
                    event["minute"],
                    event["home_possession"],
                    event["away_possession"]
                )
            
            elif event_type == "shots":
                return self.producer.publish_shots(
                    match_id,
                    event["minute"],
                    event["home_shots"],
                    event["home_shots_on_target"],
                    event["away_shots"],
                    event["away_shots_on_target"]
                )
            
            elif event_type == "corner":
                return self.producer.publish_corner(
                    match_id,
                    event["minute"],
                    event["team"]
                )
            
            elif event_type == "foul":
                return self.producer.publish_foul(
                    match_id,
                    event["minute"],
                    event["team"],
                    event["player"]
                )
            
            return True
        
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False

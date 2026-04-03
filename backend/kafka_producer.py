"""
Kafka Producer for Match Events
Publishes simulated match events to Kafka topics for consumption
"""
import json
import logging
from typing import Optional, Dict
from kafka import KafkaProducer
from kafka.errors import KafkaError
import time

logger = logging.getLogger(__name__)


class MatchEventProducer:
    """
    Publishes match events to Kafka topics
    
    Topics:
    - match-events.goals
    - match-events.cards
    - match-events.possession
    - match-events.shots
    - match-events.fouls
    - match-events.corners
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka bootstrap server address
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic_prefix = "match-events"
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[self.bootstrap_servers],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                request_timeout_ms=10000
            )
            logger.info(f"✓ Connected to Kafka at {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.producer = None
    
    def is_connected(self) -> bool:
        """Check if producer is connected"""
        return self.producer is not None
    
    def publish_event(self, event_type: str, match_id: int, event_data: Dict) -> bool:
        """
        Publish event to appropriate topic
        
        Args:
            event_type: Type of event (goal, card, possession, shots, foul, corner)
            match_id: Match ID
            event_data: Event data dictionary
        
        Returns:
            True if published successfully
        """
        if not self.producer:
            logger.warning("Producer not connected")
            return False
        
        try:
            topic = f"{self.topic_prefix}.{event_type}"
            
            # Add metadata
            message = {
                "match_id": match_id,
                "event_type": event_type,
                "timestamp": time.time(),
                **event_data
            }
            
            # Publish with match_id as key for partitioning
            future = self.producer.send(
                topic,
                value=message,
                key=str(match_id).encode('utf-8')
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=5)
            logger.debug(
                f"Event published to {record_metadata.topic} "
                f"partition {record_metadata.partition} at offset {record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error publishing event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False
    
    def publish_goal(self, match_id: int, minute: int, team: str, player: str) -> bool:
        """Publish goal event"""
        return self.publish_event("goals", match_id, {
            "minute": minute,
            "team": team,
            "player": player,
            "goal_type": "open_play"
        })
    
    def publish_card(self, match_id: int, minute: int, team: str, player: str, 
                    card_type: str) -> bool:
        """Publish card event"""
        event_type = "yellow_cards" if card_type == "yellow" else "red_cards"
        return self.publish_event(event_type, match_id, {
            "minute": minute,
            "team": team,
            "player": player,
            "card_type": card_type
        })
    
    def publish_possession(self, match_id: int, minute: int, home_pct: float, 
                          away_pct: float) -> bool:
        """Publish possession update"""
        return self.publish_event("possession", match_id, {
            "minute": minute,
            "home_possession": home_pct,
            "away_possession": away_pct
        })
    
    def publish_shots(self, match_id: int, minute: int, home_shots: int, 
                     home_on_target: int, away_shots: int, 
                     away_on_target: int) -> bool:
        """Publish shots update"""
        return self.publish_event("shots", match_id, {
            "minute": minute,
            "home_shots": home_shots,
            "home_on_target": home_on_target,
            "away_shots": away_shots,
            "away_on_target": away_on_target
        })
    
    def publish_corner(self, match_id: int, minute: int, team: str) -> bool:
        """Publish corner event"""
        return self.publish_event("corners", match_id, {
            "minute": minute,
            "team": team
        })
    
    def publish_foul(self, match_id: int, minute: int, team: str, player: str) -> bool:
        """Publish foul event"""
        return self.publish_event("fouls", match_id, {
            "minute": minute,
            "team": team,
            "player": player
        })
    
    def close(self):
        """Close producer connection"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Producer closed")


# ============ RETRY WITH MOCK FALLBACK ============

class MockKafkaProducer:
    """Mock producer for testing without Kafka server"""
    
    def __init__(self):
        """Initialize mock producer"""
        self.messages = []
        logger.info("Using MockKafkaProducer (Kafka not available)")
    
    def is_connected(self) -> bool:
        return True
    
    def publish_event(self, event_type: str, match_id: int, event_data: Dict) -> bool:
        """Store event in memory"""
        message = {
            "match_id": match_id,
            "event_type": event_type,
            "timestamp": time.time(),
            **event_data
        }
        self.messages.append(message)
        logger.debug(f"Mock published: {event_type} for match {match_id}")
        return True
    
    def publish_goal(self, match_id: int, minute: int, team: str, player: str) -> bool:
        return self.publish_event("goals", match_id, {
            "minute": minute, "team": team, "player": player
        })
    
    def publish_card(self, match_id: int, minute: int, team: str, player: str, 
                    card_type: str) -> bool:
        event_type = "yellow_cards" if card_type == "yellow" else "red_cards"
        return self.publish_event(event_type, match_id, {
            "minute": minute, "team": team, "player": player, "card_type": card_type
        })
    
    def publish_possession(self, match_id: int, minute: int, home_pct: float, 
                          away_pct: float) -> bool:
        return self.publish_event("possession", match_id, {
            "minute": minute, "home_possession": home_pct, "away_possession": away_pct
        })
    
    def publish_shots(self, match_id: int, minute: int, home_shots: int, 
                     home_on_target: int, away_shots: int, 
                     away_on_target: int) -> bool:
        return self.publish_event("shots", match_id, {
            "minute": minute,
            "home_shots": home_shots, "home_on_target": home_on_target,
            "away_shots": away_shots, "away_on_target": away_on_target
        })
    
    def publish_corner(self, match_id: int, minute: int, team: str) -> bool:
        return self.publish_event("corners", match_id, {"minute": minute, "team": team})
    
    def publish_foul(self, match_id: int, minute: int, team: str, player: str) -> bool:
        return self.publish_event("fouls", match_id, {
            "minute": minute, "team": team, "player": player
        })
    
    def close(self):
        logger.info("Mock producer closed")
    
    def get_messages(self):
        """Get all messages (for testing)"""
        return self.messages


def get_producer(bootstrap_servers: str = "localhost:9092") -> 'MatchEventProducer':
    """
    Get Kafka producer with fallback to mock
    
    Args:
        bootstrap_servers: Kafka bootstrap servers
    
    Returns:
        MatchEventProducer or MockKafkaProducer
    """
    producer = MatchEventProducer(bootstrap_servers)
    
    if not producer.is_connected():
        logger.warning("Falling back to MockKafkaProducer")
        return MockKafkaProducer()
    
    return producer

"""
Kafka Consumer for Match Events
Consumes events from Kafka topics and updates match state
"""
import json
import logging
import threading
from typing import Optional, Callable, Dict, List
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import time

logger = logging.getLogger(__name__)


class MatchEventConsumer:
    """
    Consumes match events from Kafka and triggers callbacks
    
    Subscribes to all match-events.* topics and processes events
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092", 
                 group_id: str = "match-state-consumer"):
        """
        Initialize Kafka consumer
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            group_id: Consumer group ID
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self.running = False
        self.thread = None
        self.callbacks: Dict[str, List[Callable]] = {
            "goals": [],
            "yellow_cards": [],
            "red_cards": [],
            "possession": [],
            "shots": [],
            "fouls": [],
            "corners": []
        }
        self._connect()
    
    def _connect(self):
        """Connect to Kafka"""
        try:
            self.consumer = KafkaConsumer(
                bootstrap_servers=[self.bootstrap_servers],
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                session_timeout_ms=30000,
                request_timeout_ms=10000
            )
            logger.info(f"✓ Connected to Kafka consumer at {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka consumer: {e}")
            self.consumer = None
    
    def is_connected(self) -> bool:
        """Check if consumer is connected"""
        return self.consumer is not None
    
    def subscribe(self, topics: List[str]) -> bool:
        """
        Subscribe to topics
        
        Args:
            topics: List of topic names
        
        Returns:
            True if subscribed
        """
        if not self.consumer:
            logger.warning("Consumer not connected")
            return False
        
        try:
            self.consumer.subscribe(topics)
            logger.info(f"Subscribed to topics: {topics}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to topics: {e}")
            return False
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        Register callback for event type
        
        Args:
            event_type: Type of event (goals, cards, etc.)
            callback: Function to call when event received
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.debug(f"Registered callback for {event_type}")
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def _process_event(self, event: Dict):
        """
        Process single event and trigger callbacks
        
        Args:
            event: Event data dictionary
        """
        event_type = event.get("event_type")
        
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {e}")
        else:
            logger.warning(f"No callbacks registered for {event_type}")
    
    def start(self):
        """Start consuming events in background thread"""
        if self.running:
            logger.warning("Consumer already running")
            return
        
        # Subscribe to all match-events topics
        if not self.subscribe([
            "match-events.goals",
            "match-events.yellow_cards",
            "match-events.red_cards",
            "match-events.possession",
            "match-events.shots",
            "match-events.fouls",
            "match-events.corners"
        ]):
            logger.error("Failed to subscribe to topics")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()
        logger.info("Consumer started")
    
    def _consume_loop(self):
        """Main consumption loop"""
        if not self.consumer:
            logger.error("Consumer not connected")
            return
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    event = message.value
                    logger.debug(f"Received event: {event['event_type']} for match {event['match_id']}")
                    self._process_event(event)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """Stop consuming events"""
        if not self.running:
            logger.warning("Consumer not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Consumer stopped")
    
    def close(self):
        """Close consumer connection"""
        self.stop()
        if self.consumer:
            self.consumer.close()
            logger.info("Consumer closed")


# ============ MOCK CONSUMER FOR TESTING ============

class MockKafkaConsumer:
    """Mock consumer for testing without Kafka server"""
    
    def __init__(self):
        """Initialize mock consumer"""
        self.running = False
        self.callbacks = {
            "goals": [],
            "yellow_cards": [],
            "red_cards": [],
            "possession": [],
            "shots": [],
            "fouls": [],
            "corners": []
        }
        logger.info("Using MockKafkaConsumer (Kafka not available)")
    
    def is_connected(self) -> bool:
        return True
    
    def subscribe(self, topics: List[str]) -> bool:
        logger.info(f"Mock subscribed to: {topics}")
        return True
    
    def register_callback(self, event_type: str, callback: Callable):
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def start(self):
        self.running = True
        logger.info("Mock consumer started")
    
    def stop(self):
        self.running = False
        logger.info("Mock consumer stopped")
    
    def close(self):
        pass
    
    def trigger_event(self, event_type: str, event_data: Dict):
        """Manually trigger event for testing"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                callback(event_data)


def get_consumer(bootstrap_servers: str = "localhost:9092",
                group_id: str = "match-state-consumer") -> 'MatchEventConsumer':
    """
    Get Kafka consumer with fallback to mock
    
    Args:
        bootstrap_servers: Kafka bootstrap servers
        group_id: Consumer group ID
    
    Returns:
        MatchEventConsumer or MockKafkaConsumer
    """
    consumer = MatchEventConsumer(bootstrap_servers, group_id)
    
    if not consumer.is_connected():
        logger.warning("Falling back to MockKafkaConsumer")
        return MockKafkaConsumer()
    
    return consumer

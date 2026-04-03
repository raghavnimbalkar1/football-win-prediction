"""
Redis Cache Module for Live Match State Storage
Handles all caching operations using Redis
"""
import redis
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from models import LiveMatchState, PredictionSnapshot

logger = logging.getLogger(__name__)

# ============ REDIS CONNECTION ============

class RedisCache:
    """
    Redis connection and cache management for match state
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Initialize Redis connection
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
        """
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,  # Decode bytes to strings
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            self.client.ping()
            logger.info(f"✓ Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            logger.error(f"✗ Failed to connect to Redis: {e}")
            raise
    
    # ============ MATCH STATE OPERATIONS ============
    
    def save_match_state(self, match_state: LiveMatchState, ttl: int = 86400) -> bool:
        """
        Save live match state to Redis
        
        Args:
            match_state: LiveMatchState object
            ttl: Time to live in seconds (default: 24 hours)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"match:{match_state.match_id}:state"
            value = json.dumps(match_state.to_dict())
            self.client.setex(key, ttl, value)
            logger.debug(f"Saved state for match {match_state.match_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving match state: {e}")
            return False
    
    def get_match_state(self, match_id: int) -> Optional[LiveMatchState]:
        """
        Retrieve live match state from Redis
        
        Args:
            match_id: Match ID
        
        Returns:
            LiveMatchState object or None if not found
        """
        try:
            key = f"match:{match_id}:state"
            data = self.client.get(key)
            
            if data is None:
                logger.debug(f"No state found for match {match_id}")
                return None
            
            state_dict = json.loads(data)
            return LiveMatchState.from_dict(state_dict)
        except Exception as e:
            logger.error(f"Error retrieving match state: {e}")
            return None
    
    def delete_match_state(self, match_id: int) -> bool:
        """Delete match state from cache"""
        try:
            key = f"match:{match_id}:state"
            self.client.delete(key)
            logger.debug(f"Deleted state for match {match_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting match state: {e}")
            return False
    
    # ============ PREDICTION SNAPSHOT OPERATIONS ============
    
    def save_prediction_snapshot(
        self, 
        match_id: int, 
        snapshot: PredictionSnapshot,
        ttl: int = 86400
    ) -> bool:
        """
        Save prediction snapshot for a match minute
        
        Args:
            match_id: Match ID
            snapshot: PredictionSnapshot object
            ttl: Time to live in seconds
        
        Returns:
            True if successful
        """
        try:
            key = f"match:{match_id}:prediction:{snapshot.minute}"
            value = json.dumps(snapshot.to_dict())
            self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Error saving prediction snapshot: {e}")
            return False
    
    def get_prediction_snapshot(self, match_id: int, minute: int) -> Optional[Dict]:
        """Retrieve prediction snapshot for a specific minute"""
        try:
            key = f"match:{match_id}:prediction:{minute}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error retrieving prediction snapshot: {e}")
            return None
    
    def get_all_prediction_snapshots(self, match_id: int) -> list:
        """Get all prediction snapshots for a match"""
        try:
            pattern = f"match:{match_id}:prediction:*"
            keys = self.client.keys(pattern)
            snapshots = []
            
            for key in sorted(keys):
                data = self.client.get(key)
                if data:
                    snapshots.append(json.loads(data))
            
            return snapshots
        except Exception as e:
            logger.error(f"Error retrieving prediction snapshots: {e}")
            return []
    
    # ============ BASE XG CACHING ============
    
    def save_base_xg(
        self,
        match_id: int,
        home_xg: float,
        away_xg: float,
        ttl: int = 86400
    ) -> bool:
        """
        Cache the base xG values for a match (calculated at match start)
        
        Args:
            match_id: Match ID
            home_xg: Home team base xG
            away_xg: Away team base xG
            ttl: Time to live
        
        Returns:
            True if successful
        """
        try:
            key = f"match:{match_id}:base_xg"
            value = json.dumps({
                "home_xg": home_xg,
                "away_xg": away_xg,
                "created_at": datetime.now().isoformat()
            })
            self.client.setex(key, ttl, value)
            logger.debug(f"Saved base xG for match {match_id}: {home_xg} - {away_xg}")
            return True
        except Exception as e:
            logger.error(f"Error saving base xG: {e}")
            return False
    
    def get_base_xg(self, match_id: int) -> Optional[Dict]:
        """Retrieve base xG values for a match"""
        try:
            key = f"match:{match_id}:base_xg"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error retrieving base xG: {e}")
            return None
    
    # ============ ACTIVE MATCHES TRACKING ============
    
    def add_active_match(self, match_id: int, home_team: str, away_team: str) -> bool:
        """Add match to active matches set"""
        try:
            key = "active_matches"
            self.client.sadd(key, f"{match_id}:{home_team}:{away_team}")
            self.client.expire(key, 86400)
            return True
        except Exception as e:
            logger.error(f"Error adding active match: {e}")
            return False
    
    def get_active_matches(self) -> list:
        """Get all currently active matches"""
        try:
            key = "active_matches"
            matches = self.client.smembers(key)
            return list(matches)
        except Exception as e:
            logger.error(f"Error retrieving active matches: {e}")
            return []
    
    def remove_active_match(self, match_id: int, home_team: str, away_team: str) -> bool:
        """Remove match from active set"""
        try:
            key = "active_matches"
            self.client.srem(key, f"{match_id}:{home_team}:{away_team}")
            return True
        except Exception as e:
            logger.error(f"Error removing active match: {e}")
            return False
    
    # ============ GENERAL OPERATIONS ============
    
    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def clear_match_data(self, match_id: int) -> bool:
        """Clear all data for a specific match"""
        try:
            pattern = f"match:{match_id}:*"
            keys = self.client.keys(pattern)
            
            if keys:
                self.client.delete(*keys)
                logger.info(f"Cleared {len(keys)} Redis keys for match {match_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error clearing match data: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get Redis server statistics"""
        try:
            info = self.client.info()
            return {
                "connected_clients": info.get("connected_clients"),
                "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "total_commands_processed": info.get("total_commands_processed"),
                "uptime_seconds": info.get("uptime_in_seconds"),
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {}


# ============ GLOBAL CACHE INSTANCE ============
# Will be initialized when first needed

_cache_instance: Optional[RedisCache] = None

def get_redis_cache() -> RedisCache:
    """
    Get or create the global Redis cache instance (Singleton pattern)
    
    Returns:
        RedisCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance

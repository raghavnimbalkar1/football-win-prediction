"""
Mock Redis Cache for testing without Redis server
Stores data in memory instead of Redis
"""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MockRedisCache:
    """
    In-memory cache implementation to replace Redis for testing/development
    Useful when Redis is not available or for unit testing
    """
    
    def __init__(self):
        """Initialize in-memory storage"""
        self.data: Dict[str, tuple] = {}  # Key -> (value, expiry)
        logger.info("✓ Using in-memory cache (MockRedisCache)")
    
    def set(self, key: str, value: str, ex: int = None) -> bool:
        """Set a key with optional expiry"""
        if ex:
            expiry = datetime.now() + timedelta(seconds=ex)
        else:
            expiry = None
        self.data[key] = (value, expiry)
        return True
    
    def setex(self, key: str, ex: int, value: str) -> bool:
        """Set a key with expiry time"""
        return self.set(key, value, ex)
    
    def get(self, key: str) -> Optional[str]:
        """Get a key, return None if expired or not found"""
        if key not in self.data:
            return None
        
        value, expiry = self.data[key]
        
        # Check if expired
        if expiry and datetime.now() > expiry:
            del self.data[key]
            return None
        
        return value
    
    def delete(self, *keys) -> int:
        """Delete one or more keys"""
        deleted = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                deleted += 1
        return deleted
    
    def keys(self, pattern: str) -> list:
        """Get keys matching pattern (basic glob support)"""
        import fnmatch
        return [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]
    
    def sadd(self, key: str, *members) -> int:
        """Add members to a set"""
        if key not in self.data:
            self.data[key] = (set(), None)
        
        value, expiry = self.data[key]
        if not isinstance(value, set):
            value = set()
        
        added = 0
        for member in members:
            if member not in value:
                value.add(member)
                added += 1
        
        self.data[key] = (value, expiry)
        return added
    
    def srem(self, key: str, *members) -> int:
        """Remove members from a set"""
        if key not in self.data:
            return 0
        
        value, expiry = self.data[key]
        if not isinstance(value, set):
            return 0
        
        removed = 0
        for member in members:
            if member in value:
                value.remove(member)
                removed += 1
        
        self.data[key] = (value, expiry)
        return removed
    
    def smembers(self, key: str) -> set:
        """Get all members of a set"""
        if key not in self.data:
            return set()
        
        value, expiry = self.data[key]
        if isinstance(value, set):
            return value
        return set()
    
    def expire(self, key: str, ex: int) -> int:
        """Set expiry for a key"""
        if key not in self.data:
            return 0
        
        value, _ = self.data[key]
        expiry = datetime.now() + timedelta(seconds=ex)
        self.data[key] = (value, expiry)
        return 1
    
    def ping(self) -> bool:
        """Health check"""
        return True
    
    def info(self) -> dict:
        """Get cache statistics"""
        return {
            "connected_clients": 1,
            "used_memory": len(str(self.data)) * 8,
            "total_commands_processed": 0,
            "uptime_in_seconds": 0,
        }

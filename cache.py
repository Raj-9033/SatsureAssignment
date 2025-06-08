import threading
import time
from typing import Any, Optional, Dict
from dataclasses import dataclass
from collections import OrderedDict
import logging

@dataclass
class CacheEntry:
    value: Any
    expiry: float
    created_at: float

class ThreadSafeCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize a thread-safe cache with LRU eviction and TTL support.
        
        Args:
            max_size (int): Maximum number of items in cache
            default_ttl (int): Default time-to-live in seconds
        """
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._default_ttl = default_ttl
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expired_removals = 0
        
        # Setup cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._stop_cleanup = threading.Event()
        self._cleanup_thread.start()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Add or update a key-value pair in the cache.
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (Optional[int]): Time-to-live in seconds
        """
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]
            
            # Check if we need to evict
            if len(self._cache) >= self._max_size:
                self._evict_lru()
            
            # Calculate expiry time
            if ttl is not None and ttl < 0:
                ttl = self._default_ttl
            expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
            
            # Add new entry
            self._cache[key] = CacheEntry(
                value=value,
                expiry=expiry,
                created_at=time.time()
            )
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key (str): Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if time.time() > entry.expiry:
                del self._cache[key]
                self._expired_removals += 1
                self._misses += 1
                return None
            
            # Update access order
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value

    def delete(self, key: str) -> bool:
        """
        Remove a key from the cache.
        
        Args:
            key (str): Cache key
            
        Returns:
            bool: True if key was present and removed
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def _evict_lru(self) -> None:
        """Evict the least recently used item."""
        if self._cache:
            self._cache.popitem(last=False)
            self._evictions += 1

    def _cleanup_expired(self) -> None:
        """Background thread to periodically remove expired entries."""
        while not self._stop_cleanup.is_set():
            with self._lock:
                current_time = time.time()
                expired_keys = [
                    key for key, entry in self._cache.items()
                    if current_time > entry.expiry
                ]
                for key in expired_keys:
                    del self._cache[key]
                    self._expired_removals += 1
                    self.logger.info(f"Removed expired key: {key}")
            
            # Sleep for a short interval
            time.sleep(0.1)  # Reduced sleep time for more frequent cleanup

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, Any]: Dictionary containing cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.2f}%",
                'total_requests': total_requests,
                'current_size': len(self._cache),
                'max_size': self._max_size,
                'evictions': self._evictions,
                'expired_removals': self._expired_removals
            }

    def __del__(self):
        """Cleanup when the cache is destroyed."""
        self._stop_cleanup.set()
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join() 
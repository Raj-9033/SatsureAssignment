import unittest
import threading
import time
from cache import ThreadSafeCache

class TestCacheDetails(unittest.TestCase):
    def setUp(self):
        # Create a small cache for testing
        self.cache = ThreadSafeCache(max_size=3, default_ttl=5)
    
    def test_ttl_variations(self):
        """Test different TTL scenarios"""
        print("\nTesting TTL variations...")
        
        # Test immediate expiration
        self.cache.put("key1", "value1", ttl=1)
        time.sleep(1.1)
        self.assertIsNone(self.cache.get("key1"), "Value should be expired")
        
        # Test default TTL
        self.cache.put("key2", "value2")
        time.sleep(1)
        self.assertIsNotNone(self.cache.get("key2"), "Value should not be expired yet")
        time.sleep(4.1)
        self.assertIsNone(self.cache.get("key2"), "Value should be expired")
        
        # Test very long TTL
        self.cache.put("key3", "value3", ttl=3600)
        time.sleep(1)
        self.assertIsNotNone(self.cache.get("key3"), "Value should not be expired")

    def test_concurrent_writes(self):
        """Test concurrent write operations"""
        print("\nTesting concurrent writes...")
        
        def writer(thread_id):
            for i in range(10):
                key = f"thread{thread_id}_key{i}"
                self.cache.put(key, f"value{i}")
                time.sleep(0.01)  # Small delay to increase chance of race conditions
        
        # Create and start multiple writer threads
        threads = [threading.Thread(target=writer, args=(i,)) for i in range(3)]
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify cache size hasn't exceeded max_size
        stats = self.cache.get_stats()
        self.assertLessEqual(stats['current_size'], self.cache._max_size)
        print(f"Final cache size: {stats['current_size']}")

    def test_lru_eviction_pattern(self):
        """Test LRU eviction pattern"""
        print("\nTesting LRU eviction pattern...")
        
        # Fill cache
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        
        # Access pattern: key1 -> key3 -> key2
        self.cache.get("key1")
        self.cache.get("key3")
        self.cache.get("key2")
        
        # Add new key, should evict key1 (least recently used)
        self.cache.put("key4", "value4")
        
        # Verify key1 is evicted
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNotNone(self.cache.get("key2"))
        self.assertIsNotNone(self.cache.get("key3"))
        self.assertIsNotNone(self.cache.get("key4"))

    def test_stats_accuracy(self):
        """Test statistics accuracy"""
        print("\nTesting statistics accuracy...")
        
        # Perform operations
        self.cache.put("key1", "value1")
        self.cache.get("key1")  # Hit
        self.cache.get("key1")  # Hit
        self.cache.get("key2")  # Miss
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        self.cache.put("key4", "value4")  # Should cause eviction
        
        stats = self.cache.get_stats()
        print(f"Cache stats: {stats}")
        
        self.assertEqual(stats['hits'], 2)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['current_size'], 3)
        self.assertGreaterEqual(stats['evictions'], 1)

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\nTesting error handling...")
        
        # Test invalid TTL
        self.cache.put("key1", "value1", ttl=-1)  # Should use default TTL
        self.assertIsNotNone(self.cache.get("key1"))
        
        # Test None values
        self.cache.put("key2", None)
        self.assertIsNone(self.cache.get("key2"))
        
        # Test empty string key
        self.cache.put("", "empty key")
        self.assertEqual(self.cache.get(""), "empty key")

    def test_cleanup_thread(self):
        """Test background cleanup thread"""
        print("\nTesting cleanup thread...")
        
        # Use a cache with max_size=5 for this test
        cache = ThreadSafeCache(max_size=5, default_ttl=5)
        # Add entries with short TTL
        for i in range(5):
            cache.put(f"key{i}", f"value{i}", ttl=1)
        
        # Wait for cleanup
        time.sleep(2)
        
        # Verify entries are cleaned up
        stats = cache.get_stats()
        print(f"Cache stats after cleanup: {stats}")
        self.assertGreaterEqual(stats['expired_removals'], 5)

if __name__ == '__main__':
    unittest.main(verbosity=2) 
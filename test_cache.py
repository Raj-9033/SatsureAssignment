import unittest
import threading
import time
from cache import ThreadSafeCache

class TestThreadSafeCache(unittest.TestCase):
    def setUp(self):
        self.cache = ThreadSafeCache(max_size=3, default_ttl=2)

    def test_basic_operations(self):
        # Test put and get
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Test delete
        self.cache.delete("key1")
        self.assertIsNone(self.cache.get("key1"))
        
        # Test clear
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_ttl_expiration(self):
        # Test with custom TTL
        self.cache.put("key1", "value1", ttl=1)
        time.sleep(1.1)  # Wait for expiration
        self.assertIsNone(self.cache.get("key1"))
        
        # Test with default TTL
        self.cache.put("key2", "value2")
        time.sleep(2.1)  # Wait for expiration
        self.assertIsNone(self.cache.get("key2"))

    def test_lru_eviction(self):
        # Fill cache to max size
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        
        # Access key1 to make it most recently used
        self.cache.get("key1")
        
        # Add new key, should evict key2 (least recently used)
        self.cache.put("key4", "value4")
        self.assertIsNone(self.cache.get("key2"))
        self.assertIsNotNone(self.cache.get("key1"))
        self.assertIsNotNone(self.cache.get("key3"))
        self.assertIsNotNone(self.cache.get("key4"))

    def test_concurrent_access(self):
        def worker():
            for i in range(100):
                self.cache.put(f"key{i}", f"value{i}")
                self.cache.get(f"key{i}")
                time.sleep(0.001)  # Small delay to increase chance of race conditions

        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify cache is in a consistent state
        stats = self.cache.get_stats()
        self.assertLessEqual(stats['current_size'], self.cache._max_size)

    def test_stats(self):
        # Perform some operations
        self.cache.put("key1", "value1")
        self.cache.get("key1")  # Hit
        self.cache.get("key2")  # Miss
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        self.cache.put("key4", "value4")  # Should cause eviction
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['current_size'], 3)
        self.assertGreaterEqual(stats['evictions'], 1)

if __name__ == '__main__':
    unittest.main() 
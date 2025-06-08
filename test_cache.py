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

    def test_thread_specific_concurrent_access(self):
        # Create a larger cache for this test
        self.cache = ThreadSafeCache(max_size=1000, default_ttl=300)
        
        # Use an event to synchronize thread completion
        completion_event = threading.Event()
        threads_completed = 0
        completion_lock = threading.Lock()
        
        def worker(thread_id):
            nonlocal threads_completed
            try:
                for i in range(100):
                    self.cache.put(f"thread_{thread_id}:item_{i}", f"data_{i}")
                    self.cache.get(f"thread_{thread_id}:item_{i//2}")
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            finally:
                with completion_lock:
                    threads_completed += 1
                    if threads_completed == 5:  # All threads completed
                        completion_event.set()

        # Create multiple threads with different thread IDs
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        completion_event.wait(timeout=10)  # Wait up to 10 seconds
        
        # Verify cache is in a consistent state
        stats = self.cache.get_stats()
        self.assertLessEqual(stats['current_size'], self.cache._max_size)
        
        # Verify that some items from each thread are still in cache
        for thread_id in range(5):
            found_items = 0
            for i in range(100):
                if self.cache.get(f"thread_{thread_id}:item_{i}") is not None:
                    found_items += 1
            self.assertGreater(found_items, 0, f"Thread {thread_id} items not found in cache")
            
        # Print cache statistics for debugging
        print("\nCache Statistics after concurrent access:")
        for key, value in stats.items():
            print(f"{key}: {value}")

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
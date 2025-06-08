import time
import threading
from cache import ThreadSafeCache

def run_performance_test():
    # Create cache with larger size for performance testing
    cache = ThreadSafeCache(max_size=10000, default_ttl=300)
    
    # Test basic operations performance
    print("Testing basic operations...")
    start_time = time.time()
    
    # Put operations
    for i in range(1000):
        cache.put(f"key{i}", f"value{i}")
    
    # Get operations
    for i in range(1000):
        cache.get(f"key{i}")
    
    basic_ops_time = time.time() - start_time
    print(f"Basic operations (1000 puts + 1000 gets): {basic_ops_time:.2f} seconds")
    
    # Test eviction performance
    print("\nTesting eviction performance...")
    start_time = time.time()
    
    for i in range(11000):  # Exceed max size
        cache.put(f"evict_key{i}", f"evict_value{i}")
    
    eviction_time = time.time() - start_time
    print(f"Eviction operations (11000 puts): {eviction_time:.2f} seconds")
    
    # Test concurrent access performance
    print("\nTesting concurrent access performance...")
    start_time = time.time()
    
    def worker(thread_id):
        for i in range(1000):
            cache.put(f"thread_{thread_id}:item_{i}", f"data_{i}")
            cache.get(f"thread_{thread_id}:item_{i//2}")
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    concurrent_time = time.time() - start_time
    print(f"Concurrent operations (5 threads, 1000 ops each): {concurrent_time:.2f} seconds")
    
    # Print final statistics
    print("\nFinal Cache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    run_performance_test() 
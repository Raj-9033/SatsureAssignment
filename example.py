from cache import ThreadSafeCache
import time
import threading

def main():
    # Create a cache with max size 5 and default TTL of 10 seconds
    cache = ThreadSafeCache(max_size=5, default_ttl=10)
    
    # Basic usage
    print("Basic Usage:")
    cache.put("name", "John")
    print(f"Name: {cache.get('name')}")
    
    # Custom TTL
    print("\nCustom TTL:")
    cache.put("temp", "data", ttl=2)
    print(f"Temp data: {cache.get('temp')}")
    time.sleep(2.1)
    print(f"Temp data after 2.1s: {cache.get('temp')}")
    
    # LRU eviction
    print("\nLRU Eviction:")
    for i in range(6):
        cache.put(f"key{i}", f"value{i}")
        print(f"Added key{i}")
    
    print("\nCache contents after eviction:")
    for i in range(6):
        value = cache.get(f"key{i}")
        print(f"key{i}: {value}")
    
    # Concurrent access
    print("\nConcurrent Access:")
    def worker(worker_id):
        for i in range(3):
            key = f"worker{worker_id}_key{i}"
            cache.put(key, f"value{i}")
            time.sleep(0.1)
            value = cache.get(key)
            print(f"Worker {worker_id} - {key}: {value}")
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    # Print final statistics
    print("\nCache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main() 
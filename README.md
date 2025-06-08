# Thread-Safe In-Memory Cache

A Python implementation of a thread-safe in-memory cache with TTL support and LRU eviction policy.

## Features

- Thread-safe operations using `threading.RLock`
- TTL (Time-To-Live) support with configurable expiration
- LRU (Least Recently Used) eviction policy
- Size-limited cache with automatic eviction
- Background cleanup thread for expired entries
- Comprehensive statistics tracking
- O(1) operations for get, put, and delete
- Type hints and documentation

## Requirements

- Python 3.7+
- No external dependencies

## Installation

No installation required. Simply copy the `cache.py` file to your project.

## Usage

```python
from cache import ThreadSafeCache

# Create a cache with max size 1000 and default TTL of 300 seconds
cache = ThreadSafeCache(max_size=1000, default_ttl=300)

# Basic operations
cache.put("key", "value")
value = cache.get("key")
cache.delete("key")
cache.clear()

# Custom TTL
cache.put("key", "value", ttl=60)  # Expires in 60 seconds

# Get statistics
stats = cache.get_stats()
print(stats)
```

## Design Decisions

### Concurrency Model
- Uses `threading.RLock` for thread safety
- All operations are atomic and thread-safe
- Background cleanup thread for expired entries

### Eviction Strategy
- LRU (Least Recently Used) policy
- O(1) eviction using OrderedDict
- Automatic eviction when cache size exceeds max_size

### Performance Considerations
- O(1) operations for all main functions
- Minimal locking scope for better concurrency
- Efficient cleanup of expired entries

## Running Tests

```bash
python -m unittest test_cache.py
```

## Running Example

```bash
python example.py
```

## Sample Stats Output

```python
{
    'hits': 100,
    'misses': 20,
    'hit_rate': '83.33%',
    'total_requests': 120,
    'current_size': 950,
    'max_size': 1000,
    'evictions': 50,
    'expired_removals': 30
}
```

## License

MIT License 
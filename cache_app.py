import streamlit as st
import time
import threading
from typing import Any, Optional, Dict
from dataclasses import dataclass
from collections import OrderedDict
import logging
import pandas as pd
import plotly.express as px

# Cache Implementation
@dataclass
class CacheEntry:
    value: Any
    expiry: float
    created_at: float

class ThreadSafeCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
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
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            
            if len(self._cache) >= self._max_size:
                self._evict_lru()
            
            if ttl is not None and ttl < 0:
                ttl = self._default_ttl
            expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
            
            self._cache[key] = CacheEntry(
                value=value,
                expiry=expiry,
                created_at=time.time()
            )
            
            self._cache.move_to_end(key)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            if time.time() > entry.expiry:
                del self._cache[key]
                self._expired_removals += 1
                self._misses += 1
                return None
            
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def _evict_lru(self) -> None:
        if self._cache:
            self._cache.popitem(last=False)
            self._evictions += 1

    def _cleanup_expired(self) -> None:
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
            time.sleep(0.1)

    def get_stats(self) -> Dict[str, Any]:
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
        self._stop_cleanup.set()
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join()

# Streamlit Frontend
def main():
    # Initialize cache in session state
    if 'cache' not in st.session_state:
        st.session_state.cache = ThreadSafeCache(max_size=10, default_ttl=30)

    # Page config
    st.set_page_config(page_title="Cache Visualization", layout="wide")
    st.title("Thread-Safe Cache Visualization")

    # Sidebar for cache operations
    st.sidebar.header("Cache Operations")

    # Put operation
    st.sidebar.subheader("Add to Cache")
    key = st.sidebar.text_input("Key")
    value = st.sidebar.text_input("Value")
    ttl = st.sidebar.number_input("TTL (seconds)", min_value=1, value=30)
    if st.sidebar.button("Add to Cache"):
        if key and value:
            st.session_state.cache.put(key, value, ttl)
            st.sidebar.success(f"Added {key} to cache!")
        else:
            st.sidebar.error("Key and value are required!")

    # Get operation
    st.sidebar.subheader("Get from Cache")
    get_key = st.sidebar.text_input("Key to retrieve")
    if st.sidebar.button("Get Value"):
        if get_key:
            value = st.session_state.cache.get(get_key)
            if value is not None:
                st.sidebar.success(f"Value: {value}")
            else:
                st.sidebar.error("Key not found or expired!")
        else:
            st.sidebar.error("Please enter a key!")

    # Delete operation
    st.sidebar.subheader("Delete from Cache")
    delete_key = st.sidebar.text_input("Key to delete")
    if st.sidebar.button("Delete"):
        if delete_key:
            if st.session_state.cache.delete(delete_key):
                st.sidebar.success(f"Deleted {delete_key} from cache!")
            else:
                st.sidebar.error("Key not found!")
        else:
            st.sidebar.error("Please enter a key!")

    # Main content area
    col1, col2 = st.columns(2)

    # Cache Statistics
    with col1:
        st.header("Cache Statistics")
        stats = st.session_state.cache.get_stats()
        
        # Create metrics
        st.metric("Current Size", stats['current_size'])
        st.metric("Max Size", stats['max_size'])
        st.metric("Hit Rate", stats['hit_rate'])
        st.metric("Total Requests", stats['total_requests'])
        
        # Create a bar chart for hits and misses
        hits_misses = pd.DataFrame({
            'Type': ['Hits', 'Misses'],
            'Count': [stats['hits'], stats['misses']]
        })
        fig = px.bar(hits_misses, x='Type', y='Count', title='Cache Hits vs Misses')
        st.plotly_chart(fig)

    # Cache Contents
    with col2:
        st.header("Cache Contents")
        
        # Get all entries
        entries = []
        with st.session_state.cache._lock:
            for key, entry in st.session_state.cache._cache.items():
                entries.append({
                    'Key': key,
                    'Value': entry.value,
                    'TTL': round(entry.expiry - time.time(), 1),
                    'Created': time.strftime('%H:%M:%S', time.localtime(entry.created_at))
                })
        
        if entries:
            df = pd.DataFrame(entries)
            st.dataframe(df)
            
            # Create a bar chart for TTL
            fig = px.bar(df, x='Key', y='TTL', title='Remaining TTL for Each Entry')
            st.plotly_chart(fig)
        else:
            st.info("Cache is empty!")

    # Auto-refresh
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main() 
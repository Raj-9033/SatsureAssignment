import streamlit as st
import time
from cache import ThreadSafeCache
import pandas as pd
import plotly.express as px

# Initialize cache
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
st.experimental_rerun() 
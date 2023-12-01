import atexit
import threading
from collections import OrderedDict
import time

# Initialize event_cache and lock object for thread safety
event_cache = OrderedDict()
cache_lock = threading.Lock()
cache_cleanup_interval = 7.2 * 60 * 60  # 7.2 hours


# Cache cleanup function
def cleanup_event_cache():
    while True:
        time.sleep(cache_cleanup_interval)
        with cache_lock:
            for event_id, event_data in list(event_cache.items()):
                if time.time() - event_data['timestamp'] >= cache_cleanup_interval:
                    del event_cache[event_id]
                else:
                    break

# Start cache cleanup thread
cleanup_thread = threading.Thread(target=cleanup_event_cache)

def stop_cleanup_thread():
    cleanup_thread.join()

atexit.register(stop_cleanup_thread)
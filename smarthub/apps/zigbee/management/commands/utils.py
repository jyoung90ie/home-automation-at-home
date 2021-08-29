def get_cache_key(device_identifier: str):
    """Returns a cache key for retrieving from/storing in the cache"""
    return ":".join(["mqtt", str(device_identifier)])

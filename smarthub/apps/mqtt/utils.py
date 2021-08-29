"""MQTT utility functions module"""
from . import defines


def get_cache_key(device_identifier: str):
    """Returns a cache key for retrieving from/storing in the cache"""
    return ":".join([defines.CACHE_KEY_PREFIX, str(device_identifier)])

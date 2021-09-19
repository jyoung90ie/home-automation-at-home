from django.test import TestCase

from ..defines import CACHE_KEY_PREFIX
from ..utils import get_cache_key


class TestGetCacheKey(TestCase):
    def test_return_value(self):
        device_identifier = "Dummy-Device-Identifier"

        cache_key = get_cache_key(device_identifier=device_identifier)

        self.assertEqual(cache_key, f"{CACHE_KEY_PREFIX}:{device_identifier}")

from django.test import TestCase
from django.test.utils import override_settings

_test_settings = {
    # Use a faster password hasher for unit tests to improve performance
    'PASSWORD_HASHERS': ('django.contrib.auth.hashers.MD5PasswordHasher',),

    'STATIC_URL': 'http://localhost:/static/',

    # Without this we'd need to invalidate the cache before every test.
    'USE_OBJECT_CACHES': False,
    'USE_ECO_CACHE': False,
}


@override_settings(**_test_settings)
class OTMTestCase(TestCase):
    """
    Base class for OTM2 tests.
    """
    def assertValidationErrorDictContainsKey(self, ve, key):
        self.assertTrue(key in ve.error_dict,
                        'Expected "%s" to be a key in error_dict %s' %
                        (key, ve.error_dict))

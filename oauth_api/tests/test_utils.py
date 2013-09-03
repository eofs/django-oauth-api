from django.core.validators import ValidationError
from django.test import TestCase

from oauth_api.utils import validate_uris


class TestUtils(TestCase):
    def test_valid_uris(self):
        uris = 'http://localhost http://example.com http://example.com/?key=val'
        try:
            validate_uris(uris)
        except ValidationError:
            self.fail('validate_uris() raises ValidationError unexpectedly when providing valid URIs!')

    def test_invalid_uris(self):
        uris = 'http://example.com http://example'
        self.assertRaises(ValidationError, validate_uris, uris)


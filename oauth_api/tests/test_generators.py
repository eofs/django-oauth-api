from django.test import TestCase

from oauth_api.generators import (BaseGenerator, ClientIdGenerator, ClientSecretGenerator,
                                  generate_client_id, generate_client_secret)
from oauth_api.settings import oauth_api_settings


class MockGenerator(BaseGenerator):
    def hash(self):
        return 42


class TestGenerators(TestCase):
    def tearDown(self):
        oauth_api_settings.CLIENT_ID_GENERATOR = ClientIdGenerator
        oauth_api_settings.CLIENT_SECRET_GENERATOR = ClientSecretGenerator

    def test_client_id_generator(self):
        g = oauth_api_settings.CLIENT_ID_GENERATOR()
        self.assertEqual(len(g.hash()), 64)

        oauth_api_settings.CLIENT_ID_GENERATOR = MockGenerator
        self.assertEqual(generate_client_id(), 42)

    def test_client_secret_generator(self):
        g = oauth_api_settings.CLIENT_SECRET_GENERATOR()
        self.assertEqual(len(g.hash()), 128)

        oauth_api_settings.CLIENT_SECRET_GENERATOR = MockGenerator
        self.assertEqual(generate_client_secret(), 42)

    def test_invalid_generator(self):
        g = BaseGenerator()
        self.assertRaises(NotImplementedError, g.hash)

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from oauth_api.models import AccessToken, get_application_model


Appliation = get_application_model()
User = get_user_model()


class TestModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dev_user = User.objects.create_user('dev_user', 'dev_user@example.com', '1234')

    def test_allow_scopes(self):
        app = Appliation.objects.create(
            name='Test App',
            redirect_uris='http://localhost http://example.com',
            user=self.dev_user,
            client_type=Appliation.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Appliation.GRANT_AUTHORIZATION_CODE,
        )

        now = timezone.now()
        expires = now + timezone.timedelta(days=7)
        
        access_token = AccessToken.objects.create(
            user=self.dev_user,
            scope='read write',
            expires=expires,
            token='',
            application=app,
        )

        self.assertTrue(access_token.allow_scopes(['read', 'write']))
        self.assertTrue(access_token.allow_scopes(['write', 'read']))
        self.assertTrue(access_token.allow_scopes(['write', 'read', 'read']))
        self.assertTrue(access_token.allow_scopes([]))
        self.assertFalse(access_token.allow_scopes(['read', 'invalid']))

    def test_access_token_user_may_be_none(self):
        app = Appliation.objects.create(
            name='Test App',
            redirect_uris='http://localhost http://example.com',
            user=self.dev_user,
            client_type=Appliation.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Appliation.GRANT_AUTHORIZATION_CODE,
        )

        access_token = AccessToken.objects.create(token='1234567890', application=app,
                                                  expires=timezone.now())
        self.assertIsNone(access_token.user)

    def test_default_redirect_uri(self):
        app = Appliation(
            name='Test App',
            redirect_uris='http://localhost http://example.com',
            user=self.dev_user,
            client_type=Appliation.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Appliation.GRANT_AUTHORIZATION_CODE
        )

        self.assertEqual(app.default_redirect_uri, 'http://localhost')

    def test_valid_redirect_uri(self):
        app = Appliation(
            name='Test App',
            redirect_uris='http://localhost http://example.com',
            user=self.dev_user,
            client_type=Appliation.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Appliation.GRANT_AUTHORIZATION_CODE
        )

        self.assertTrue(app.redirect_uri_allowed('http://localhost'))

    def test_invalid_redirect_uri(self):
        app = Appliation(
            name='Test App',
            redirect_uris='http://localhost http://example.com',
            user=self.dev_user,
            client_type=Appliation.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Appliation.GRANT_AUTHORIZATION_CODE
        )

        self.assertFalse(app.redirect_uri_allowed('http://invalid.local.host'))

    def test_grant_authorization_code(self):
        app = Appliation(
            name='Test App',
            redirect_uris='',
            user=self.dev_user,
            client_type=Appliation.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Appliation.GRANT_AUTHORIZATION_CODE,
        )

        self.assertRaises(ValidationError, app.full_clean)

    def test_grant_implicit(self):
        app = Appliation(
            name='Test App',
            redirect_uris='',
            user=self.dev_user,
            client_type=Appliation.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Appliation.GRANT_IMPLICIT,
        )

        self.assertRaises(ValidationError, app.full_clean)


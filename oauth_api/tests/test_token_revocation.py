from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from django.utils import timezone

from rest_framework import status

from rest_framework.test import APIRequestFactory

from oauth_api.models import get_application_model, AccessToken, RefreshToken
from oauth_api.tests.utils import TestCaseUtils

Application = get_application_model()
User = get_user_model()


class BaseTest(TestCaseUtils):
    def setUp(self):
        self.test_user = User.objects.create_user('test_user', 'test_user@example.com', '1234')
        self.dev_user = User.objects.create_user('dev_user', 'dev_user@example.com', '1234')
        self.application = Application(
            name='Test Application',
            redirect_uris='http://localhost http://example.com',
            user=self.dev_user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        self.application.save()

        self.public_application = Application(
            name='Public Test Application',
            redirect_uris='http://localhost http://example.com',
            user=self.dev_user,
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE)
        self.public_application.save()

        self.factory = APIRequestFactory()


class AccessTokenRevocationTest(BaseTest):
    def setUp(self):
        super(AccessTokenRevocationTest, self).setUp()
        self.access_token = AccessToken.objects.create(user=self.test_user, token='conf1234567890',
                                                       application=self.application,
                                                       expires=timezone.now() + timezone.timedelta(days=1),
                                                       scope='read write')

        self.public_access_token = AccessToken.objects.create(user=self.test_user, token='pub1234567890',
                                                              application=self.public_application,
                                                              expires=timezone.now() + timezone.timedelta(days=1),
                                                              scope='read write')

    def test_revoke_access_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'token': self.access_token.token,
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AccessToken.objects.filter(pk=self.access_token.pk).exists())

    def test_revoke_access_token_with_public_app(self):
        data = {
            'client_id': self.public_application.client_id,
            'token': self.public_access_token.token,
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AccessToken.objects.filter(pk=self.public_access_token.pk).exists())

    def test_revoke_access_token_without_app(self):
        data = {
            'token': self.access_token.token,
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(AccessToken.objects.filter(pk=self.access_token.pk).exists())

    def test_revoke_access_token_with_hint(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'token': self.access_token.token,
            'token_type_hint': 'access_token',
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AccessToken.objects.filter(pk=self.access_token.pk).exists())

    def test_revoke_access_token_with_invalid_hint(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'token': self.access_token.token,
            'token_type_hint': 'foo_bar',
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AccessToken.objects.filter(pk=self.access_token.pk).exists())

    def test_revoke_access_token_with_mismatching_app(self):
        """
        Test token revocation using mismatching application
        """
        other_token = AccessToken.objects.create(user=self.test_user, token='1029384756',
                                                 application=self.public_application,
                                                 expires=timezone.now() + timezone.timedelta(days=1),
                                                 scope='read write')

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'token': other_token.token,
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AccessToken.objects.filter(pk=other_token.pk).exists())
        self.assertTrue(AccessToken.objects.filter(pk=self.access_token.pk).exists())


class RefreshTokenRevocationTest(BaseTest):
    def setUp(self):
        super(RefreshTokenRevocationTest, self).setUp()
        self.access_token = AccessToken.objects.create(user=self.test_user, token='conf1234567890',
                                                       application=self.application,
                                                       expires=timezone.now() + timezone.timedelta(days=1),
                                                       scope='read write')

        self.refresh_token = RefreshToken.objects.create(user=self.test_user, token='conf0987654321',
                                                         application=self.application,
                                                         access_token=self.access_token,
                                                         expires=timezone.now() + timezone.timedelta(days=3))

        self.public_access_token = AccessToken.objects.create(user=self.test_user, token='pub1234567890',
                                                              application=self.public_application,
                                                              expires=timezone.now() + timezone.timedelta(days=1),
                                                              scope='read write')

        self.public_refresh_token = RefreshToken.objects.create(user=self.test_user, token='pub0987654321',
                                                                application=self.public_application,
                                                                access_token=self.public_access_token,
                                                                expires=timezone.now() + timezone.timedelta(days=3))

    def test_revoke_refresh_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'token': self.refresh_token.token,
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AccessToken.objects.filter(pk=self.access_token.pk).exists())
        self.assertFalse(RefreshToken.objects.filter(pk=self.refresh_token.pk).exists())

    def test_revoke_refresh_token_with_public_app(self):
        data = {
            'client_id': self.public_application.client_id,
            'token': self.public_refresh_token.token,
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AccessToken.objects.filter(pk=self.public_access_token.pk).exists())
        self.assertFalse(RefreshToken.objects.filter(pk=self.public_refresh_token.pk).exists())

    def test_revoke_refresh_token_without_app(self):
        data = {
            'token': self.refresh_token.token,
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(AccessToken.objects.filter(pk=self.access_token.pk).exists())
        self.assertTrue(RefreshToken.objects.filter(pk=self.refresh_token.pk).exists())

    def test_revoke_refresh_token_with_hint(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'token': self.refresh_token.token,
            'token_type_hint': 'refresh_token',
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AccessToken.objects.filter(pk=self.access_token.pk).exists())
        self.assertFalse(RefreshToken.objects.filter(pk=self.refresh_token.pk).exists())

    def test_revoke_access_token_with_invalid_hint(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'token': self.refresh_token.token,
            'token_type_hint': 'foo_bar',
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AccessToken.objects.filter(pk=self.access_token.pk).exists())
        self.assertFalse(RefreshToken.objects.filter(pk=self.refresh_token.pk).exists())

    def test_revoke_access_token_with_mismatching_app(self):
        """
        Test token revocation using mismatching application
        """
        other_access_token = AccessToken.objects.create(user=self.test_user, token='1029384756',
                                                        application=self.public_application,
                                                        expires=timezone.now() + timezone.timedelta(days=1),
                                                        scope='read write')

        other_refresh_token = RefreshToken.objects.create(user=self.test_user, token='1122334455',
                                                          application=self.public_application,
                                                          access_token=other_access_token,
                                                          expires=timezone.now() + timezone.timedelta(days=3))

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'token': other_refresh_token.token,
            'token_type_hint': 'refresh_token',
        }
        response = self.client.post(reverse('oauth_api:revoke-token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AccessToken.objects.filter(pk=other_access_token.pk).exists())
        self.assertTrue(AccessToken.objects.filter(pk=self.access_token.pk).exists())
        self.assertTrue(RefreshToken.objects.filter(pk=other_access_token.pk).exists())
        self.assertTrue(RefreshToken.objects.filter(pk=self.refresh_token.pk).exists())

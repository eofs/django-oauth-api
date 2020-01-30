from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from oauth_api.models import get_application_model
from oauth_api.settings import oauth_api_settings
from oauth_api.tests.views import RESPONSE_DATA
from oauth_api.tests.utils import TestCaseUtils

Application = get_application_model()
User = get_user_model()


class BaseTest(TestCaseUtils, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create_user('test_user', 'test_user@example.com', '1234')
        cls.dev_user = User.objects.create_user('dev_user', 'dev_user@example.com', '1234')
        cls.application = Application(
            name='Test Application',
            redirect_uris='http://localhost http://example.com',
            user=cls.dev_user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_PASSWORD,
        )
        cls.application.save()

    def scopes_valid(self, scopes, required):
        provided_scopes = set(scopes.split())
        resource_scopes = set(required)

        return provided_scopes.issubset(resource_scopes)


class TestResourceOwnerTokenView(BaseTest):
    def test_basic_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
        }
        response = self.client.post(reverse('oauth_api:token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_auth_as_data(self):
        """
        Authenticate by sending client_id and client_secret as part of data payload
        """
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'client_id': self.application.client_id,
            'client_secret': self.application.client_secret,
        }
        response = self.client.post(reverse('oauth_api:token'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_auth(self):
        """
        Request token with invalid user credentials
        """
        data = {
            'grant_type': 'password',
            'username': 'invalid',
            'password': 'invalid',
            'client_id': self.application.client_id,
            'client_secret': self.application.client_secret,
        }
        response = self.client.post(reverse('oauth_api:token'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_client(self):
        """
        Request token with invalid client credentials
        """
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'client_id': 'invalid',
            'client_secret': 'invalid',
        }
        response = self.client.post(reverse('oauth_api:token'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_default_scope_request(self):
        """
        Test valid token request
        """
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
        }
        response = self.client.post(reverse('oauth_api:token'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token_type'], 'Bearer')
        self.assertTrue(self.scopes_valid(response.data['scope'], oauth_api_settings.SCOPES))
        self.assertEqual(response.data['expires_in'], oauth_api_settings.ACCESS_TOKEN_EXPIRATION)

    def test_valid_scope_request(self):
        """
        Test for valid scopes
        """
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'scope': 'read',
        }
        response = self.client.post(reverse('oauth_api:token'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token_type'], 'Bearer')
        self.assertTrue(self.scopes_valid(response.data['scope'], oauth_api_settings.SCOPES))
        self.assertEqual(response.data['expires_in'], oauth_api_settings.ACCESS_TOKEN_EXPIRATION)

    def test_invalid_scope_request(self):
        """
        Test for invalid scopes
        """
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'scope': 'BANANA',
        }
        response = self.client.post(reverse('oauth_api:token'), data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestResourceOwnerResourceAccess(BaseTest):
    def test_resouce_access(self):
        """
        Request an access token and try to fetch data using it
        """
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
        }
        response = self.client.post(reverse('oauth_api:token'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        access_token = response.data['access_token']

        # Update Basic Auth information
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-view'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_denied_resource_access(self):
        """
        Request an access token and try to fetch data using it
        """
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'scope': 'read',
        }
        response = self.client.post(reverse('oauth_api:token'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        access_token = response.data['access_token']

        # Update Basic Auth information
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-view'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

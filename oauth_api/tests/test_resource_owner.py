import base64

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from oauth_api.models import get_application_model
from oauth_api.settings import oauth_api_settings
from oauth_api.tests.views import RESPONSE_DATA

Application = get_application_model()
User = get_user_model()


class BaseTest(APITestCase):
    def setUp(self):
        self.test_user = User.objects.create_user('test_user', 'test_user@example.com', '1234')
        self.dev_user = User.objects.create_user('dev_user', 'dev_user@example.com', '1234')
        self.application = Application(
            name='Test Application',
            redirect_uris='http://localhost http://example.com',
            user=self.dev_user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_PASSWORD,
        )
        self.application.save()

    def get_basic_auth(self, username, password):
        payload = '%s:%s' % (username, password)
        auth = base64.b64encode(payload.encode('utf-8')).decode('utf-8')
        return 'Basic {0}'.format(auth)

    def scopes_valid(self, scopes, required):
        provided_scopes = set(scopes.split())
        resource_scopes = set(required)

        return provided_scopes.issubset(resource_scopes)

class TestResourceOwnerTokenView(BaseTest):
    def test_basic_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        url = reverse('oauth_api:token')
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_auth_as_data(self):
        """
        Authenticate by sending client_id and client_secret as part of data payload
        """
        url = reverse('oauth_api:token')
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'client_id': self.application.client_id,
            'client_secret': self.application.client_secret,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_auth(self):
        """
        Request token with invalid user credentials
        """
        url = reverse('oauth_api:token')
        data = {
            'grant_type': 'password',
            'username': 'invalid',
            'password': 'invalid',
            'client_id': self.application.client_id,
            'client_secret': self.application.client_secret,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_client(self):
        """
        Request token with invalid client credentials
        """
        url = reverse('oauth_api:token')
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'client_id': 'invalid',
            'client_secret': 'invalid',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_default_scope_request(self):
        """
        Test valid token request
        """
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        url = reverse('oauth_api:token')
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
        }
        response = self.client.post(url, data)

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
        url = reverse('oauth_api:token')
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'scope': 'read',
        }
        response = self.client.post(url, data)

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
        url = reverse('oauth_api:token')
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'scope': 'BANANA',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resouce_access(self):
        """
        Request an access token and try to fetch data using it
        """
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        url = reverse('oauth_api:token')
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        access_token = response.data['access_token']

        # Update Basic Auth information
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        url = reverse('resource-view')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_denied_resource_access(self):
        """
        Request an access token and try to fetch data using it
        """
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))
        url = reverse('oauth_api:token')
        data = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': '1234',
            'scope': 'read',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        access_token = response.data['access_token']

        # Update Basic Auth information
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        url = reverse('resource-view')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.urls import reverse

from oauthlib.oauth2 import (InvalidClientIdError, MissingClientIdError,
                             InvalidRedirectURIError, MismatchingRedirectURIError)

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
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_IMPLICIT,
        )
        cls.application.save()

    def parse_fragments(self, url):
        return parse_qs(urlparse(url).fragment)


class TestImplicit(BaseTest):
    def test_valid_client(self):
        """
        Test for valid client information
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': self.application.client_id,
            'response_type': 'token',
            'redirect_uri': 'http://localhost',
            'scope': 'read write',
            'state': 'random_state_string',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('form', response.context)
        form = response.context['form']

        self.assertEqual(form['redirect_uri'].value(), 'http://localhost')
        self.assertEqual(form['state'].value(), 'random_state_string')
        self.assertEqual(form['scopes'].value(), 'read write')
        self.assertEqual(form['client_id'].value(), self.application.client_id)

    def test_invalid_client(self):
        """
        Test for invalid client information
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': 'invalid',
            'response_type': 'token',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('error', response.context)
        error = response.context['error']

        self.assertTrue(isinstance(error, InvalidClientIdError))

    def test_missing_client(self):
        """
        Test for missing client information
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'response_type': 'token',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('error', response.context)
        error = response.context['error']

        self.assertTrue(isinstance(error, MissingClientIdError))

    def test_default_redirect_uri(self):
        """
        Test for default redirect_uri if user-agent did not provide any
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': self.application.client_id,
            'response_type': 'token',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('form', response.context)
        form = response.context['form']

        self.assertEqual(form['redirect_uri'].value(), 'http://localhost')

    def test_forbidden_redirect_uri(self):
        """
        Test for forbidden redirect_uri (Not defined in list of allowed URIs)
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': self.application.client_id,
            'response_type': 'token',
            'redirect_uri': 'http://invalid.local.host',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('error', response.context)
        error = response.context['error']

        self.assertTrue(isinstance(error, MismatchingRedirectURIError))

    def test_invalid_redirect_uri(self):
        """
        Test for malformed redirect_uri value
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': self.application.client_id,
            'response_type': 'token',
            'redirect_uri': 'invalid',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('error', response.context)
        error = response.context['error']

        self.assertTrue(isinstance(error, InvalidRedirectURIError))

    def test_post_allow(self):
        """
        Test for resource owner authorized the client
        """
        self.client.login(username='test_user', password='1234')

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://localhost',
            'response_type': 'token',
            'allow': True,
        }

        response = self.client.post(reverse('oauth_api:authorize'), data=form_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertIn('http://localhost#', response['Location'])
        self.assertIn('access_token=', response['Location'])
        self.assertIn('state=random_state_string', response['Location'])
        self.assertIn('expires_in=%s' % oauth_api_settings.ACCESS_TOKEN_EXPIRATION, response['Location'])

    def test_post_denied(self):
        """
        Test for resource owner did not authorize the client
        """
        self.client.login(username='test_user', password='1234')

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://localhost',
            'response_type': 'token',
            'allow': False,
        }

        response = self.client.post(reverse('oauth_api:authorize'), data=form_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('error=access_denied', response['Location'])


class TestImplicitResourceAccess(BaseTest):
    def test_access_allowed(self):
        """
        Test for accessing resource using valid access token
        """
        self.client.login(username='test_user', password='1234')

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://localhost',
            'response_type': 'token',
            'allow': True,
        }

        response = self.client.post(reverse('oauth_api:authorize'), data=form_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        fragments = self.parse_fragments(response['Location'])
        access_token = fragments['access_token'].pop()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-view'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_access_denied(self):
        """
        Test for accessing resource using invalid access token
        """
        self.client.force_authenticate(user=self.test_user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid')

        response = self.client.get(reverse('resource-view'))
        self.client.force_authenticate(user=None)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

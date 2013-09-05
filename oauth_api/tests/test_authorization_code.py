from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from oauthlib.oauth2 import (InvalidClientIdError, MissingClientIdError,
                             InvalidRedirectURIError, MismatchingRedirectURIError)

from rest_framework import status
from rest_framework.test import APITestCase

from oauth_api.models import get_application_model


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
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        self.application.save()


class TestAuthorizationCode(BaseTest):
    def test_invalid_client(self):
        """
        Test for invalid client information
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': 'invalid',
            'response_type': 'code',
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
            'response_type': 'code',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('error', response.context)
        error = response.context['error']

        self.assertTrue(isinstance(error, MissingClientIdError))

    def test_valid_client(self):
        """
        Test for valid client information
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': self.application.client_id,
            'response_type': 'code',
            'state': 'random_state_string',
            'scope': 'read write',
            'redirect_uri': 'http://localhost',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('form', response.context)
        form = response.context['form']

        self.assertEqual(form['redirect_uri'].value(), 'http://localhost')
        self.assertEqual(form['state'].value(), 'random_state_string')
        self.assertEqual(form['scopes'].value(), 'read write')
        self.assertEqual(form['client_id'].value(), self.application.client_id)

    def test_invalid_response_type(self):
        """
        Test for invalid response_type
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': self.application.client_id,
            'response_type': 'invalid',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('error=unauthorized_client', response['Location'])

    def test_missing_response_type(self):
        """
        Test for missing response_type
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': self.application.client_id,
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('error=invalid_request', response['Location'])

    def test_default_redirect_uri(self):
        """
        Test for default redirect uri
        """
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': self.application.client_id,
            'response_type': 'code',
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
            'response_type': 'code',
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
            'response_type': 'code',
            'redirect_uri': 'invalid',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('error', response.context)
        error = response.context['error']

        self.assertTrue(isinstance(error, InvalidRedirectURIError))

    def test_authorization_code_post_allow(self):
        """
        Test for resource owner authorized the client
        """
        self.client.login(username='test_user', password='1234')

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://localhost',
            'response_type': 'code',
            'allow': True,
        }

        response = self.client.post(reverse('oauth_api:authorize'), data=form_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('http://localhost?', response['Location'])
        self.assertIn('state=random_state_string', response['Location'])
        self.assertIn('code=', response['Location'])

    def test_authorization_code_post_denied(self):
        """
        Test for resource owner did not authorize the client
        """
        self.client.login(username='test_user', password='1234')

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://localhost',
            'response_type': 'code',
            'allow': False,
        }

        response = self.client.post(reverse('oauth_api:authorize'), data=form_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('error=access_denied', response['Location'])

    def test_authorization_code_post_invalid_response_type(self):
        """
        Test for authorization code is given for an allowed request with a invalid response_type
        """
        self.client.login(username='test_user', password='1234')

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://localhost',
            'response_type': 'invalid',
            'allow': True,
        }

        response = self.client.post(reverse('oauth_api:authorize'), data=form_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('http://localhost?error=unauthorized_client', response['Location'])

    def test_authorization_code_post_invalid_redirect_uri(self):
        """
        Test for authorization code is given for an allowed request with a invalid redirect_uri
        """
        self.client.login(username='test_user', password='1234')

        form_data = {
            'client_id': self.application.client_id,
            'state': 'random_state_string',
            'scopes': 'read write',
            'redirect_uri': 'http://invalid.local.host',
            'response_type': 'code',
            'allow': True,
        }

        response = self.client.post(reverse('oauth_api:authorize'), data=form_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

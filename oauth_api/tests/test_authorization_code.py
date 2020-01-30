from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from oauthlib.oauth2 import (InvalidClientIdError, MissingClientIdError,
                             InvalidRedirectURIError, MismatchingRedirectURIError)

from rest_framework import status

from oauth_api.models import get_application_model, AuthorizationCode, RefreshToken
from oauth_api.settings import oauth_api_settings
from oauth_api.tests.utils import TestCaseUtils
from oauth_api.tests.views import RESPONSE_DATA


Application = get_application_model()
User = get_user_model()


class BaseTest(TestCaseUtils):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create_user('test_user', 'test_user@example.com', '1234')
        cls.dev_user = User.objects.create_user('dev_user', 'dev_user@example.com', '1234')
        cls.application = Application(
            name='Test Application',
            redirect_uris='http://localhost http://example.com',
            user=cls.dev_user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        cls.application.save()

        cls.application_public = Application(
            name='Test Application (Public)',
            redirect_uris='http://localhost http://example.com',
            user=cls.dev_user,
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )
        cls.application_public.save()


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
        self.assertIn('error=unsupported_response_type', response['Location'])

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
        self.assertIn('error=unsupported_response_type', response['Location'])
        self.assertIn('state=random_state_string', response['Location'])

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


class TestAuthorizationCodeTokenView(BaseTest):
    def test_basic_auth(self):
        """
        Test for requesting access token using Basic Authentication
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token_type'], 'Bearer')
        self.assertEqual(response.data['scope'], 'read write')
        self.assertEqual(response.data['expires_in'], oauth_api_settings.ACCESS_TOKEN_EXPIRATION)

    def test_basic_auth_invalid_secret(self):
        """
        Test for requesting access toke using invalid secret via Basic Authentication
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       'invalid'))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_auth_code(self):
        """
        Test for requesting access token using invalid authorization code
        """
        self.client.login(username='test_user', password='1234')

        token_request = {
            'grant_type': 'authorization_code',
            'code': 'invalid',
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_grant_type(self):
        """
        Test for requesting access token using invalid grant_type
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'invalid',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_authorization_code(self):
        """
        Test for requesting access code when authorization code has been expired
        """
        self.client.login(username='test_user', password='1234')

        ac = AuthorizationCode(application=self.application, user=self.test_user, code='BANANA', expires=timezone.now(),
                               redirect_uri='', scope='')
        ac.save()

        token_request = {
            'grant_type': 'authorization_code',
            'code': 'BANANA',
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        """
        Test for requesting access token using refresh token
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('refresh_token' in response.data)

        # Make second token request to be sure that previous refresh token
        # remains valid.
        authorization_code = self.get_authorization_code()
        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }
        self.client.post(reverse('oauth_api:token'), token_request)

        # Request new access token using the refresh token from the first
        # request
        token_request = {
            'grant_type': 'refresh_token',
            'refresh_token': response.data['refresh_token'],
            'scope': response.data['scope'],
        }

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access_token' in response.data)

        # Refresh tokens cannot be used twice
        response = self.client.post(reverse('oauth_api:token'), token_request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue('invalid_grant' in response.data.values())

    def test_refresh_token_override_authorization(self):
        """
        Test overriding Authorization header by providing client ID and secret as param
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('refresh_token' in response.data)

        token_request = {
            'grant_type': 'refresh_token',
            'refresh_token': response.data['refresh_token'],
            'scope': response.data['scope'],
            'client_id': self.application.client_id,
            'client_secret': self.application.client_secret,
        }
        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth('invalid_client_id',
                                                                       'invalid_client_secret'))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access_token' in response.data)


    def test_refresh_token_default_scopes(self):
        """
        Test for requesting access token using refresh token while not providing any scopes
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('refresh_token' in response.data)

        token_request = {
            'grant_type': 'refresh_token',
            'refresh_token': response.data['refresh_token'],
        }

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access_token' in response.data)

    def test_refresh_token_invalid_scopes(self):
        """
        Test for requesting access token using refresh token while providing invalid scopes
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('refresh_token' in response.data)

        token_request = {
            'grant_type': 'refresh_token',
            'refresh_token': response.data['refresh_token'],
            'scope': 'read write invalid',
        }

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_repeating_request_fail(self):
        """
        Test for requesting access token using refresh token and repeating the request
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('refresh_token' in response.data)

        token_request = {
            'grant_type': 'refresh_token',
            'refresh_token': response.data['refresh_token'],
            'scope': response.data['scope'],
        }

        response = self.client.post(reverse('oauth_api:token'), token_request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(reverse('oauth_api:token'), token_request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_expired(self):
        """
        Test for requesting access token using expired refresh token
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('refresh_token' in response.data)

        token_request = {
            'grant_type': 'refresh_token',
            'refresh_token': response.data['refresh_token'],
            'scope': response.data['scope'],
        }

        # Set expiration time to expire the token
        RefreshToken.objects.update(expires=timezone.now())

        response = self.client.post(reverse('oauth_api:token'), token_request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_not_expired(self):
        """
        Test for requesting access token using refresh token with expiration date
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('refresh_token' in response.data)

        token_request = {
            'grant_type': 'refresh_token',
            'refresh_token': response.data['refresh_token'],
            'scope': response.data['scope'],
        }

        # Set expiration time to future
        RefreshToken.objects.update(expires=timezone.now() + timedelta(days=7))

        response = self.client.post(reverse('oauth_api:token'), token_request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public(self):
        """
        Test for requesting access token using client_type 'public'
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(self.application_public.client_id)

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
            'client_id': self.application_public.client_id,
        }

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['token_type'], 'Bearer')
        self.assertEqual(response.data['scope'], 'read write')
        self.assertEqual(response.data['expires_in'], oauth_api_settings.ACCESS_TOKEN_EXPIRATION)

    def test_public_with_invalid_redirect_uri(self):
        """
        Test for requesting access token using client_type 'public' and providing
        invalid redirect_uri
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(self.application_public.client_id)

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': '/../',
            'client_id': self.application_public.client_id,
        }

        response = self.client.post(reverse('oauth_api:token'), token_request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestAuthorizationCodeResourceAccess(BaseTest):
    def test_access_allowed(self):
        """
        Test for accessing resource using valid access token
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code()
        access_token = self.get_access_token(authorization_code)

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

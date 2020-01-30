from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIRequestFactory

from oauth_api.models import get_application_model, AuthorizationCode, AccessToken
from oauth_api.tests.utils import TestCaseUtils
from oauth_api.tests.views import RESPONSE_DATA, ResourceNoScopesView


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

        cls.factory = APIRequestFactory()


class TestScopes(BaseTest):
    def test_scopes_in_authorization_code(self):
        """
        Test scopes are properly saved in authorization codes
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='write scope1')

        ac = AuthorizationCode.objects.get(code=authorization_code)
        self.assertEqual(ac.scope, 'write scope1')

    def test_scopes_in_access_token(self):
        """
        Test scopes are properly saved in access tokens
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='write scope1')

        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access_token' in response.data)

        access_token = response.data['access_token']

        token = AccessToken.objects.get(token=access_token)
        self.assertEqual(token.scope, 'write scope1')


class TestScopesResourceViews(BaseTest):
    def test_required_scopes_valid(self):
        """
        Test access to resource protected by required_scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='read write')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-view'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_required_scopes_invalid(self):
        """
        Test access to resource protected by required_scope with incorrect scopes
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='write')
        access_token = self.get_access_token(authorization_code)


        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-view'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_scopes_valid(self):
        """
        Test access to resource protected by read_scopes
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='read')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-read-view'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_read_scopes_invalid(self):
        """
        Test access to resource protected by read_scopes with invalid scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='scope1')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-read-view'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_write_scopes_valid(self):
        """
        Test access to resource protected by write_scopes
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='write')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.post(reverse('resource-write-view'))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_write_scopes_invalid(self):
        """
        Test access to resource protected by write_scopes with invalid scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='scope1')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.post(reverse('resource-write-view'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_readwrite_scopes_valid_read(self):
        """
        Test access to resource protected by read_scopes and write_scopes with valid read scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='read')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-readwrite-view'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_readwrite_scopes_invalid_read(self):
        """
        Test access to resource protected by read_scopes and write_scopes with invalid read scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='scope1')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-readwrite-view'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_readwrite_scopes_valid_write(self):
        """
        Test access to resource protected by read_scopes and write_scopes with valid write scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='write')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.post(reverse('resource-readwrite-view'))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_readwrite_scopes_invalid_write(self):
        """
        Test access to resource protected by read_scopes and write_scopes with invalid write scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='scope1')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.post(reverse('resource-readwrite-view'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mixed_scopes_invalid_required(self):
        """
        Test access to resource protected by required_scopes, read_scopes and write_scopes with invalid required
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='read write')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-mixed-view'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mixed_scopes_valid_read(self):
        """
        Test access to resource protected by required_scopes, read_scopes and write_scopes with valid read scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='scope1 read')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-mixed-view'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_mixed_scopes_invalid_read(self):
        """
        Test access to resource protected by required_scopes, read_scopes and write_scopes with invalid read scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='scope1 write')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.get(reverse('resource-mixed-view'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mixed_scopes_valid_write(self):
        """
        Test access to resource protected by required_scopes, read_scopes and write_scopes with valid write scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='scope1 write')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.post(reverse('resource-readwrite-view'))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, RESPONSE_DATA)

    def test_mixed_scopes_invalid_write(self):
        """
        Test access to resource protected by required_scopes, read_scopes and write_scopes with invalid write scope
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='scope1 read')
        access_token = self.get_access_token(authorization_code)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.client.post(reverse('resource-mixed-view'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_improperly_configured(self):
        """
        Test access to resource without any required scopes defined
        """
        self.client.login(username='test_user', password='1234')
        authorization_code = self.get_authorization_code(scopes='read')
        access_token = self.get_access_token(authorization_code)

        headers = {
            'HTTP_AUTHORIZATION': 'Bearer %s' % access_token,
        }
        request = self.factory.get('/fake', **headers)

        view = ResourceNoScopesView.as_view()

        self.assertRaises(ImproperlyConfigured, view, request)

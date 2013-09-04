from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

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
        self.client.login(username='test_user', password='1234')

        query_string = {
            'client_id': 'invalid',
            'response_type': 'code',
        }
        response = self.client.get(reverse('oauth_api:authorize'), data=query_string)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_client(self):
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

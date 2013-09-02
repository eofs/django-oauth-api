import base64

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
            authorization_grant_type=Application.GRANT_PASSWORD,
        )
        self.application.save()

    def get_basic_auth(self, username, password):
        payload = '%s:%s' % (username, password)
        auth = base64.b64encode(payload.encode('utf-8')).decode('utf-8')
        return 'Basic {0}'.format(auth)


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
        response = self.client.post(url, data, format='json')
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
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

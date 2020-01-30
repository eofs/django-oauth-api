import base64
from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestCaseUtils(APITestCase):
    def get_basic_auth(self, username, password):
        payload = '%s:%s' % (username, password)
        auth = base64.b64encode(payload.encode('utf-8')).decode('utf-8')
        return 'Basic {0}'.format(auth)

    def get_authorization_code(self, client_id=None, scopes=None, redirect_uri=None, allow=True, state=None):
        """
        Utility method to get Authorization Code
        """
        form_data = {
            'client_id': client_id or self.application.client_id,
            'state': state or 'random_state_string',
            'scopes': scopes or 'read write',
            'redirect_uri': redirect_uri or 'http://localhost',
            'response_type': 'code',
            'allow': allow,
        }

        response = self.client.post(reverse('oauth_api:authorize'), data=form_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        query_dict = parse_qs(urlparse(response['Location']).query)
        return query_dict['code'].pop()

    def get_access_token(self, authorization_code, **kwargs):
        """
        Utility function to return Access Token for Authorization Code
        """
        token_request = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost',
        }
        token_request.update(kwargs)

        self.client.credentials(HTTP_AUTHORIZATION=self.get_basic_auth(self.application.client_id,
                                                                       self.application.client_secret))

        response = self.client.post(reverse('oauth_api:token'), token_request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access_token' in response.data)

        return response.data['access_token']

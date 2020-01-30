from oauthlib import oauth2
from oauthlib.common import urlencode

from rest_framework.request import Request

from oauth_api.exceptions import OAuthAPIError, FatalClientError


class OAuthHandler(object):
    def __init__(self, server):
        self.server = server

    def extract_params(self, request):

        if isinstance(request, Request):
            data = request.data
            headers = request._request.META.copy()
            uri = request._request.build_absolute_uri()
        else:
            data = urlencode(request.POST.items())
            headers = request.META.copy()
            uri = request.build_absolute_uri()

        method = request.method
        if 'wsgi.input' in headers:
            del headers['wsgi.input']
        if 'wsgi.errors' in headers:
            del headers['wsgi.errors']
        # OAuthLib looks for 'Authorization'
        if 'HTTP_AUTHORIZATION' in headers:
            headers['Authorization'] = headers['HTTP_AUTHORIZATION']
        return uri, method, data, headers

    def create_authorization_response(self, request, scopes, credentials, allow):
        try:
            if not allow:
                raise oauth2.AccessDeniedError()

            credentials['user'] = request.user

            headers, body, status = self.server.create_authorization_response(
                uri=credentials['redirect_uri'], scopes=scopes, credentials=credentials)
            uri = headers.get('Location', None)

            return uri, headers, body, status
        except oauth2.FatalClientError as error:
            raise FatalClientError(error=error, redirect_uri=credentials['redirect_uri'])
        except oauth2.OAuth2Error as error:
            raise OAuthAPIError(error=error, redirect_uri=credentials['redirect_uri'])

    def create_token_response(self, request):
        uri, method, data, headers = self.extract_params(request)
        headers, body, status = self.server.create_token_response(uri, method, data, headers)
        url = headers.get('Location', None)
        return url, headers, body, status

    def create_revocation_response(self, request):
        """
        Wrapper method to call 'create_revocation_response' in OAuthLib
        """
        uri, method, body, headers = self.extract_params(request)
        headers, body, status = self.server.create_revocation_response(uri, method, body, headers)
        url = headers.get('Location', None)
        return url, headers, body, status

    def validate_authorization_request(self, request):
        """
        Wrapper method to call `validate_authorization_request` in OAuthLib
        """
        try:
            uri, method, data, headers = self.extract_params(request)

            scopes, credentials = self.server.validate_authorization_request(
                uri, method, data, headers)

            return scopes, credentials
        except oauth2.FatalClientError as error:
            raise FatalClientError(error=error)
        except oauth2.OAuth2Error as error:
            raise OAuthAPIError(error=error)

    def verify_request(self, request, scopes):
        """
        Wrapper method to call `verify_request` in OAuthLib
        """
        uri, method, data, headers = self.extract_params(request)
        try:
            body = urlencode(data.items())
        except AttributeError:
            body = None
        valid, r = self.server.verify_request(uri, method, body, headers, scopes=scopes)
        return valid, r

from rest_framework.authentication import BaseAuthentication

from oauthlib.oauth2 import Server

from oauth_api.handlers import OAuthHandler
from oauth_api.validators import OAuthValidator


class OAuth2Authentication(BaseAuthentication):
    """
    OAuth2 authentication backend
    """
    www_authenticate_realm = 'api'

    def authenticate(self, request):
        """
        Authenticate the request
        """
        server = Server(OAuthValidator())
        handler = OAuthHandler(server)
        valid, r = handler.verify_request(request, scopes=[])

        if valid:
            return r.user, r.access_token
        else:
            return None

    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header data
        """
        return 'Bearer realm="%s"' % self.www_authenticate_realm

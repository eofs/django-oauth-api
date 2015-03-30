import base64

from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone

from oauthlib.oauth2 import RequestValidator

from oauth_api.models import get_application_model, AccessToken, AuthorizationCode, RefreshToken, AbstractApplication
from oauth_api.settings import oauth_api_settings


GRANT_TYPE_MAPPING = {
    'authorization_code': (AbstractApplication.GRANT_AUTHORIZATION_CODE,),
    'password': (AbstractApplication.GRANT_PASSWORD,),
    'client_credentials': (AbstractApplication.GRANT_CLIENT_CREDENTIALS,),
    'refresh_token': (AbstractApplication.GRANT_AUTHORIZATION_CODE, AbstractApplication.GRANT_PASSWORD,
                      AbstractApplication.GRANT_CLIENT_CREDENTIALS)
}


class OAuthValidator(RequestValidator):

    def _get_application(self, client_id, request):
        """
        Load application instance for given client_id and store it in request as 'client' attribute
        """
        assert hasattr(request, 'client'), "'client' attribute missing from 'request'"

        Application = get_application_model()

        try:
            request.client = request.client or Application.objects.get(client_id=client_id)
            return request.client
        except Application.DoesNotExist:
            return None

    def _authenticate_client_basic(self, request):
        """
        Try authenticating the client using HTTP Basic Authentication method
        """
        auth = request.headers.get('HTTP_AUTHORIZATION', None)

        if not auth:
            return False

        auth_type, auth_string = auth.split(' ')
        if not auth_type == 'Basic':
            return False

        encoding = request.encoding or 'utf-8'

        auth_string_decoded = base64.b64decode(auth_string).decode(encoding)
        client_id, client_secret = auth_string_decoded.split(':', 1)

        if self._get_application(client_id, request) is None:
            return False
        elif request.client.client_secret != client_secret:
            return False
        else:
            return True

    def _authenticate_client_body(self, request):
        """
        Try authenticating the client using values from request body
        """
        client_id = request.client_id
        client_secret = request.client_secret

        if not client_id:
            return False

        if self._get_application(client_id, request) is None:
            return False
        elif request.client.client_secret != client_secret:
            return False
        else:
            return True

    def authenticate_client(self, request, *args, **kwargs):
        """
        Try to authenticate the client.
        """
        authenticated = self._authenticate_client_basic(request)

        if not authenticated:
            authenticated = self._authenticate_client_body(request)

        return authenticated

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        """
        Ensure client_id belong to a non-confidential client.
        A non-confidential client is one that is not required to authenticate through other means, such as using HTTP Basic.
        """
        if self._get_application(client_id, request) is not None:
            return request.client.client_type != AbstractApplication.CLIENT_CONFIDENTIAL
        return False

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, *args, **kwargs):
        """
        Ensure client is authorized to redirect to the redirect_uri requested.
        """
        auth_code = AuthorizationCode.objects.get(application=client, code=code)
        return auth_code.redirect_uri_allowed(redirect_uri)

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        """
        Get the default redirect URI for the client.
        """
        return request.client.default_redirect_uri

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        """
        Get the default scopes for the client.
        """
        return list(oauth_api_settings.SCOPES.keys())

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        """
        Get the list of scopes associated with the refresh token.
        """
        return request.refresh_token_object.access_token.scope

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        """
        Invalidate an authorization code after use.
        """
        auth_code = AuthorizationCode.objects.get(application=request.client, code=code)
        auth_code.delete()

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        """
        Persist the authorization_code.
        """
        expires = timezone.now() + timedelta(seconds=oauth_api_settings.ACCESS_TOKEN_EXPIRATION)
        auth_code = AuthorizationCode(application=request.client, user=request.user, code=code['code'],
                      expires=expires, redirect_uri=request.redirect_uri,
                      scope=' '.join(request.scopes))
        auth_code.save()
        return request.redirect_uri

    def save_bearer_token(self, token, request, *args, **kwargs):
        """
        Persist the Bearer token.
        """
        if request.refresh_token_object:
            # Remove used refresh token
            try:
                RefreshToken.objects.get(token=request.refresh_token).delete()
            except RefreshToken.DoesNotExist:
                # Already deleted?
                assert()

        expires = timezone.now() + timedelta(seconds=oauth_api_settings.ACCESS_TOKEN_EXPIRATION)
        if request.grant_type == 'client_credentials':
            request.user = request.client.user

        access_token = AccessToken(
            user=request.user,
            scope=token['scope'],
            expires=expires,
            token=token['access_token'],
            application=request.client)
        access_token.save()

        if 'refresh_token' in token:
            if oauth_api_settings.REFRESH_TOKEN_EXPIRATION is not None:
                expires = timezone.now() + timedelta(seconds=oauth_api_settings.REFRESH_TOKEN_EXPIRATION)
            else:
                expires = None
            refresh_token = RefreshToken(
                user=request.user,
                token=token['refresh_token'],
                expires=expires,
                application=request.client,
                access_token=access_token)
            refresh_token.save()

        return request.client.default_redirect_uri

    def validate_bearer_token(self, token, scopes, request):
        """
        Ensure the Bearer token is valid and authorized access to scopes.
        """
        if token is None:
            return False

        try:
            access_token = AccessToken.objects.select_related('application', 'user').get(token=token)
            if access_token.is_valid(scopes):
                request.client = access_token.application
                request.user = access_token.user
                request.scopes = scopes

                # Required when autenticating using OAuth2Authentication
                request.access_token = access_token
                return True
            return False
        except AccessToken.DoesNotExist:
            return False

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """
        Check that and Application exists with given client_id.
        """
        return self._get_application(client_id, request) is not None

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        """
        Ensure the authorization_code is valid and assigned to client.
        """
        try:
            auth_code = AuthorizationCode.objects.select_related('user').get(application=client, code=code)
            if not auth_code.is_expired:
                request.scopes = auth_code.scope.split(' ')
                request.user = auth_code.user
                return True
            return False
        except AuthorizationCode.DoesNotExist:
            return False

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        """
        Ensure client is authorized to use the grant_type requested.
        """
        assert(grant_type in GRANT_TYPE_MAPPING)
        return request.client.authorization_grant_type in GRANT_TYPE_MAPPING[grant_type]

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        """
        Ensure client is authorized to redirect to the redirect_uri requested.
        """
        return request.client.redirect_uri_allowed(redirect_uri)

    def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
        """
        Ensure the Bearer token is valid and authorized access to scopes.
        """
        try:
            rt = RefreshToken.objects.select_related('user').get(token=refresh_token)
            if not rt.is_expired:
                request.user = rt.user
                request.refresh_token_object = rt
                return rt.application == client
            return False
        except RefreshToken.DoesNotExist:
            return False

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        """
        Ensure client is authorized to use the response_type requested.
        Authorization Endpoint Response Types registry is not supported.
        See http://tools.ietf.org/html/rfc6749#section-8.4
        """
        if response_type == 'code':
            return client.authorization_grant_type == AbstractApplication.GRANT_AUTHORIZATION_CODE
        elif response_type == 'token':
            return client.authorization_grant_type == AbstractApplication.GRANT_IMPLICIT
        else:
            return False

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """
        Ensure the client is authorized access to requested scopes.
        """
        return set(scopes).issubset(set(oauth_api_settings.SCOPES.keys()))

    def validate_user(self, username, password, client, request, *args, **kwargs):
        """
        Ensure the username and password is valid.
        """
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            request.user = user
            return True
        return False

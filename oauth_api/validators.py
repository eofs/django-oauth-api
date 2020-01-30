import base64
import binascii
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

    def _get_auth_string(self, request):
        auth = request.headers.get('HTTP_AUTHORIZATION', None)

        if not auth:
            return None

        splitted = auth.split(' ', 1)
        if len(splitted) != 2:
            return None

        auth_type, auth_string = splitted
        if auth_type != 'Basic':
            return None

        return auth_string

    def _authenticate_client_basic(self, request):
        """
        Try authenticating the client using HTTP Basic Authentication method
        """
        auth_string = self._get_auth_string(request)
        if not auth_string:
            return False

        try:
            encoding = request.encoding or 'utf-8'
        except AttributeError:
            encoding = 'utf-8'

        try:
            b64_decoded = base64.b64decode(auth_string)
        except (TypeError, binascii.Error):
            return False

        try:
            auth_string_decoded = b64_decoded.decode(encoding)
        except UnicodeDecodeError:
            return False

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
        try:
            client_id = request.client_id
            client_secret = request.client_secret
        except AttributeError:
            return False

        if not client_id:
            return False

        if self._get_application(client_id, request) is None:
            return False
        elif request.client.client_secret != client_secret:
            return False
        else:
            return True

    def client_authentication_required(self, request, *args, **kwargs):
        """
        Determine if client authentication is required for current request.

        According to the rfc6749, client authentication is required in the following cases:
            - Resource Owner Password Credentials Grant, when Client type is Confidential or when
              Client was issued client credentials or whenever Client provided client
              authentication, see `Section 4.3.2`_.
            - Authorization Code Grant, when Client type is Confidential or when Client was issued
              client credentials or whenever Client provided client authentication,
              see `Section 4.1.3`_.
            - Refresh Token Grant, when Client type is Confidential or when Client was issued
              client credentials or whenever Client provided client authentication, see
              `Section 6`_

        :param request: oauthlib.common.Request
        :return: True or False
        """
        if self._get_auth_string(request):
            return True

        try:
            if request.client_id and request.client_secret:
                return True
        except AttributeError:
            # Client id or secret not provided
            pass

        self._get_application(request.client_id, request)
        if request.client:
            return request.client.client_type == AbstractApplication.CLIENT_CONFIDENTIAL

        return super(OAuthValidator, self).client_authentication_required(request, *args, **kwargs)

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
        AuthorizationCode.objects.create(
            application=request.client,
            user=request.user,
            code=code['code'],
            expires=expires,
            redirect_uri=request.redirect_uri,
            scope=' '.join(request.scopes)
        )
        return request.redirect_uri

    def save_bearer_token(self, token, request, *args, **kwargs):
        """
        Persist the Bearer token.
        """
        if request.refresh_token:
            # Revoke Refresh Token (and related Access Token)
            try:
                RefreshToken.objects.get(token=request.refresh_token).revoke()
            except RefreshToken.DoesNotExist:
                # Already revoked?
                pass

        expires = timezone.now() + timedelta(seconds=oauth_api_settings.ACCESS_TOKEN_EXPIRATION)
        user = request.user
        if request.grant_type == 'client_credentials':
            user = None

        access_token = AccessToken.objects.create(
            user=user,
            scope=token['scope'],
            expires=expires,
            token=token['access_token'],
            application=request.client
        )

        if 'refresh_token' in token:
            if oauth_api_settings.REFRESH_TOKEN_EXPIRATION is not None:
                expires = timezone.now() + timedelta(seconds=oauth_api_settings.REFRESH_TOKEN_EXPIRATION)
            else:
                expires = None
            RefreshToken.objects.create(
                user=request.user,
                token=token['refresh_token'],
                expires=expires,
                application=request.client,
                access_token=access_token
            )

        return request.client.default_redirect_uri

    def revoke_token(self, token, token_type_hint, request, *args, **kwargs):
        """
        Revoke an access or refresh token.

        :param token: The token string.
        :param token_type_hint: access_token or refresh_token.
        :param request: The HTTP Request (oauthlib.common.Request)
        """
        if token_type_hint not in ['access_token', 'refresh_token']:
            token_type_hint = None

        token_types = {
            'access_token': AccessToken,
            'refresh_token': RefreshToken,
        }

        token_type = token_types.get(token_type_hint, AccessToken)

        try:
            token_type.objects.get(token=token, application=request.client).revoke()
        except token_type.DoesNotExist:
            # Lookup from all token types except from already looked up type
            other_types = (_type for _type in token_types.values() if _type != token_type)
            for other_type in other_types:
                for token in other_type.objects.filter(token=token, application=request.client):
                    token.revoke()

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

                # Required when authenticating using OAuth2Authentication
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
        assert (grant_type in GRANT_TYPE_MAPPING)
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
                request.refresh_token = rt.token
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

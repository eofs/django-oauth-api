import base64

from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone

from oauthlib.oauth2 import RequestValidator

from oauth_api.models import get_application_model, AccessToken, RefreshToken
from oauth_api.settings import oauth_api_settings


Application = get_application_model()


GRANT_TYPE_MAPPING = {
    'authorization_code': (Application.GRANT_ALLINONE, Application.GRANT_AUTHORIZATION_CODE),
    'password': (Application.GRANT_ALLINONE, Application.GRANT_PASSWORD),
    'client_credentials': (Application.GRANT_ALLINONE, Application.GRANT_CLIENT_CREDENTIALS),
    'refresh_token': (Application.GRANT_ALLINONE, Application.GRANT_AUTHORIZATION_CODE, Application.GRANT_PASSWORD,
                      Application.GRANT_CLIENT_CREDENTIALS)
}

class OAuthValidator(RequestValidator):

    def authenticate_client(self, request, *args, **kwargs):
        """
        Try to authenticate the client.
        """
        auth = request.headers.get('HTTP_AUTHORIZATION', None)

        if auth:
            auth_type, auth_string = auth.split(' ')
            encoding = request.encoding or 'utf-8'

            auth_string_decoded = base64.b64decode(auth_string).decode(encoding)
            client_id, client_secret = auth_string_decoded.split(':', 1)
        else:
            client_id = request.body.get('client_id', None)
            client_secret = request.body.get('client_secret', None)

            if not client_id or not client_secret:
                return False

        try:
            request.client = Application.objects.get(client_id=client_id, client_secret=client_secret)
            return True
        except Application.DoesNotExist:
            return False

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        """
        Get the default scopes for the client.
        """
        return oauth_api_settings.SCOPES

    def get_original_scopes(self, refresh_token, request, *args, **kwargs):
        """
        Get the list of scopes associated with the refresh token.
        """
        rt = RefreshToken.objects.get(token=refresh_token)
        return rt.access_token.scope

    def save_bearer_token(self, token, request, *args, **kwargs):
        """
        Persist the Bearer token.
        """
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
            # Discard old refresh token
            RefreshToken.objects.filter(user=request.user, application=request.client).delete()

            refresh_token = RefreshToken(
                user=request.user,
                token=token['refresh_token'],
                application=request.client,
                access_token=access_token)
            refresh_token.save()

        return request.client.default_redirect_uri

    def validate_client_id(self, client_id, request, *args, **kwargs):
        """
        Check that and Application exists with given client_id.
        """
        try:
            request.client = request.client or Application.objects.get(client_id=client_id)
            return True
        except Application.DoesNotExist:
            return False

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        """
        Ensure client is authorized to use the grant_type requested.
        """
        assert(grant_type in GRANT_TYPE_MAPPING)
        return request.client.authorization_grant_type in GRANT_TYPE_MAPPING[grant_type]

    def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
        """
        Ensure the Bearer token is valid and authorized access to scopes.
        """
        try:
            rt = RefreshToken.objects.get(token=refresh_token)
            request.user = rt.user
            return rt.application == client
        except RefreshToken.DoesNotExist:
            return False

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """
        Ensure the client is authorized access to requested scopes.
        """
        return set(scopes).issubset(set(oauth_api_settings.SCOPES))

    def validate_user(self, username, password, client, request, *args, **kwargs):
        """
        Ensure the username and password is valid.
        """
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            request.user = user
            return True
        return False

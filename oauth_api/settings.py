from django.conf import settings
from rest_framework.settings import APISettings

APP_NAME = 'OAUTH_API'
USER_SETTINGS = getattr(settings, APP_NAME, None)


DEFAULTS = {
    'ACCESS_TOKEN_EXPIRATION': 3600,  # Seconds
    'REFRESH_TOKEN_EXPIRATION': None,  # Seconds, (None == disabled)
    'APPLICATION_MODEL': 'oauth_api.Application',
    'CLIENT_ID_GENERATOR': 'oauth_api.generators.ClientIdGenerator',
    'CLIENT_SECRET_GENERATOR': 'oauth_api.generators.ClientSecretGenerator',
    'DEFAULT_HANDLER_CLASS': 'oauth_api.handlers.OAuthHandler',
    'DEFAULT_SERVER_CLASS': 'oauthlib.oauth2.Server',
    'DEFAULT_VALIDATOR_CLASS': 'oauth_api.validators.OAuthValidator',
    'SCOPES': {
        'read': 'Read access',
        'write': 'Write access',
    }
}


IMPORT_STRINGS = (
    'CLIENT_ID_GENERATOR',
    'CLIENT_SECRET_GENERATOR',
    'DEFAULT_HANDLER_CLASS',
    'DEFAULT_SERVER_CLASS',
    'DEFAULT_VALIDATOR_CLASS',
)


class OAuthApiSettings(APISettings):
    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        self._user_settings = user_settings or {}
        self.defaults = defaults or {}
        self.import_strings = import_strings or ()
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, APP_NAME, {})
        return self._user_settings


oauth_api_settings = OAuthApiSettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)
